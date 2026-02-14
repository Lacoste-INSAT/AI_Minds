"""
Synapsis Backend — Ollama LLM Client
3-tier fallback: phi4-mini → qwen2.5:3b → qwen2.5:0.5b
"""

from __future__ import annotations

import json
from typing import AsyncGenerator

import httpx
import structlog

from backend.config import settings

logger = structlog.get_logger(__name__)


class OllamaClient:
    """Async client for Ollama API with 3-tier model fallback."""

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.models = [
            settings.ollama_model_t1,
            settings.ollama_model_t2,
            settings.ollama_model_t3,
        ]
        self.active_model: str | None = None
        self.active_tier: int = 0
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(settings.ollama_timeout, connect=10.0),
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ------------------------------------------------------------------
    # Health / availability
    # ------------------------------------------------------------------

    async def is_available(self) -> bool:
        """Check if Ollama is reachable."""
        try:
            client = await self._get_client()
            resp = await client.get("/api/tags")
            return resp.status_code == 200
        except Exception:
            return False

    async def get_available_model(self) -> str | None:
        """Find the first available model from the 3-tier chain."""
        try:
            client = await self._get_client()
            resp = await client.get("/api/tags")
            if resp.status_code != 200:
                return None
            data = resp.json()
            available: set[str] = set()
            for m in data.get("models", []):
                full_name = m["name"]          # e.g. "phi4-mini:latest"
                available.add(full_name)          # exact name
                available.add(full_name.split(":")[0])  # base name without tag

            for i, model in enumerate(self.models):
                # Check various name formats
                if model in available or f"{model}:latest" in available:
                    self.active_model = model
                    self.active_tier = i + 1
                    logger.info("ollama.model_selected", model=model, tier=self.active_tier)
                    return model
        except Exception as e:
            logger.error("ollama.model_check_failed", error=str(e))

        return None

    async def get_model_info(self) -> dict:
        """Get info about the active model."""
        if not self.active_model:
            await self.get_available_model()
        return {
            "model": self.active_model,
            "tier": f"T{self.active_tier}",
            "status": "up" if self.active_model else "down",
        }

    # ------------------------------------------------------------------
    # Generate
    # ------------------------------------------------------------------

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        """Generate a completion. Falls back through tiers on failure."""
        if not self.active_model:
            await self.get_available_model()

        models_to_try = (
            self.models[self.active_tier - 1:] if self.active_tier > 0 else self.models
        )

        for model in models_to_try:
            try:
                return await self._call_generate(
                    model, prompt, system, temperature, max_tokens
                )
            except Exception as e:
                logger.warning("ollama.generate_failed", model=model, error=str(e))
                continue

        logger.error("ollama.all_tiers_failed")
        return "I'm unable to process this request right now. All model tiers are unavailable."

    async def _call_generate(
        self,
        model: str,
        prompt: str,
        system: str | None,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Make the actual /api/generate call."""
        client = await self._get_client()

        payload: dict = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system:
            payload["system"] = system

        resp = await client.post("/api/generate", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "")

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        """Chat-style completion using /api/chat."""
        if not self.active_model:
            await self.get_available_model()

        models_to_try = (
            self.models[self.active_tier - 1:] if self.active_tier > 0 else self.models
        )

        for model in models_to_try:
            try:
                return await self._call_chat(model, messages, temperature, max_tokens)
            except Exception as e:
                logger.warning("ollama.chat_failed", model=model, error=str(e))
                continue

        logger.error("ollama.all_tiers_failed")
        return "I'm unable to process this request right now."

    async def _call_chat(
        self,
        model: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
    ) -> str:
        client = await self._get_client()
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        resp = await client.post("/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "")

    # ------------------------------------------------------------------
    # Streaming
    # ------------------------------------------------------------------

    async def stream_generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """Stream tokens from Ollama."""
        if not self.active_model:
            await self.get_available_model()

        model = self.active_model or self.models[0]
        client = await self._get_client()

        payload: dict = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system:
            payload["system"] = system

        try:
            async with client.stream("POST", "/api/generate", json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            token = data.get("response", "")
                            if token:
                                yield token
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error("ollama.stream_failed", error=str(e))
            yield f"[Error: {str(e)}]"

    async def stream_chat(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """Stream tokens from Ollama chat API."""
        if not self.active_model:
            await self.get_available_model()

        model = self.active_model or self.models[0]
        client = await self._get_client()

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            async with client.stream("POST", "/api/chat", json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            token = data.get("message", {}).get("content", "")
                            if token:
                                yield token
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error("ollama.stream_chat_failed", error=str(e))
            yield f"[Error: {str(e)}]"


# Singleton
ollama_client = OllamaClient()
