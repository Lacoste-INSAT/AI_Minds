"""
Ollama Provider — Local LLM via Ollama API.

Implements the LLMProvider ABC for local inference via Ollama.
but hitting localhost:11434 instead of a proprietary API.

Model: Qwen2.5-3B-Instruct (or whatever is pulled in Ollama)
Run:   ollama pull qwen2.5:3b-instruct
"""

import asyncio
import json
from typing import AsyncIterator

import httpx

from .base_provider import LLMProvider
from ..config.settings import settings


class OllamaProvider(LLMProvider):
    def __init__(self):
        self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=settings.ollama_base_url,
                timeout=settings.ollama_timeout,
            )
        return self._client

    async def generate(self, messages: list[dict]) -> dict:
        payload = {
            "model": settings.ollama_model,
            "messages": messages,
            "stream": False,
        }
        for attempt in range(3):
            try:
                client = self._get_client()
                resp = await client.post("/api/chat", json=payload)
                if resp.is_success:
                    data = resp.json()
                    # Ollama returns {"message": {"role": "assistant", "content": "..."}}
                    # Convert to OpenAI-compatible format for base_agent._parse_llm_response
                    return {
                        "choices": [{
                            "message": {
                                "role": "assistant",
                                "content": data.get("message", {}).get("content", ""),
                            }
                        }]
                    }
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
            except (httpx.TransportError, RuntimeError) as e:
                if attempt < 2:
                    await asyncio.sleep(1)
                else:
                    return {"error": {"status_code": 0, "body": f"Ollama connection error: {e}"}}
        return {"error": {"status_code": resp.status_code, "body": resp.text}}

    async def stream(self, messages: list[dict]) -> AsyncIterator[str]:
        payload = {
            "model": settings.ollama_model,
            "messages": messages,
            "stream": True,
        }
        client = self._get_client()
        try:
            async with client.stream("POST", "/api/chat", json=payload) as resp:
                if not resp.is_success:
                    yield json.dumps({"error": {"status_code": resp.status_code}})
                    return
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    chunk = json.loads(line)
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content
                    if chunk.get("done"):
                        break
        except (httpx.TransportError, RuntimeError) as e:
            yield json.dumps({"error": {"status_code": 0, "body": str(e)}})
