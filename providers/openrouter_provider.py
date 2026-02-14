import asyncio
import json
from typing import AsyncIterator

import httpx

from .base_provider import LLMProvider
from ..config.settings import settings


class OpenRouterProvider(LLMProvider):
    def __init__(self):
        if not settings.openrouter_api_key:
            raise ValueError("OpenRouter API key not configured")
        self._client = None
    
    def _get_client(self) -> httpx.AsyncClient:
        """Get or create a fresh httpx client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=settings.openrouter_base_url,
                timeout=settings.openrouter_timeout,
            )
        return self._client
    
    async def _ensure_fresh_client(self):
        """Close existing client and create a fresh one."""
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception:
                pass
        self._client = httpx.AsyncClient(
            base_url=settings.openrouter_base_url,
            timeout=settings.openrouter_timeout,
        )
        return self._client

    def _headers(self) -> dict:
        headers = {"Authorization": f"Bearer {settings.openrouter_api_key}"}
        if settings.openrouter_http_referer:
            headers["HTTP-Referer"] = settings.openrouter_http_referer
        if settings.openrouter_app_title:
            headers["X-Title"] = settings.openrouter_app_title
        return headers

    async def generate(self, messages: list[dict]) -> dict:
        payload = {"model": settings.openrouter_model, "messages": messages}
        resp = None
        for attempt in range(3):
            try:
                client = self._get_client()
                resp = await client.post("/chat/completions", headers=self._headers(), json=payload)
                if resp.status_code != 429:
                    break
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
            except (httpx.TransportError, RuntimeError, ConnectionError) as e:
                # Connection error - get a fresh client and retry
                if attempt < 2:
                    await self._ensure_fresh_client()
                    await asyncio.sleep(1)
                else:
                    return {"error": {"status_code": 0, "body": f"Connection error: {e}"}}
        
        if resp is None:
            return {"error": {"status_code": 0, "body": "No response received"}}
        if not resp.is_success:
            return {"error": {"status_code": resp.status_code, "body": resp.text}}
        return resp.json()

    async def stream(self, messages: list[dict]) -> AsyncIterator[str]:
        payload = {"model": settings.openrouter_model, "messages": messages, "stream": True}
        client = self._get_client()
        try:
            async with client.stream(
                "POST", "/chat/completions", headers=self._headers(), json=payload
            ) as resp:
                if not resp.is_success:
                    yield json.dumps({"error": {"status_code": resp.status_code, "body": resp.text}})
                    return
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line.removeprefix("data: ")
                    if data == "[DONE]":
                        break
                    chunk = json.loads(data)
                    delta = chunk["choices"][0].get("delta", {}).get("content")
                    if delta:
                        yield delta
        except (httpx.TransportError, RuntimeError, ConnectionError) as e:
            yield json.dumps({"error": {"status_code": 0, "body": f"Connection error: {e}"}})
