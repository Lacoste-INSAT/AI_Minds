"""
Synapsis Reasoning Engine - Ollama Client
3-Tier fallback chain for CPU-only operation.
T1: phi4-mini (3.8B) -> T2: qwen2.5:3b (3.1B) -> T3: qwen2.5:0.5b (0.5B)

For CPU-only mode, we default to T3 to ensure acceptable latency.
"""
import asyncio
import time
import json
import logging
from typing import Optional

import httpx

from .models import LLMResponse, ModelTier


logger = logging.getLogger(__name__)

# Ollama API endpoint (localhost only - air-gapped)
OLLAMA_BASE_URL = "http://127.0.0.1:11434"

# Model configuration
MODEL_CONFIG = {
    ModelTier.T1: {
        "name": "phi4-mini",
        "context_length": 128000,
        "timeout_seconds": 120,  # Slower on CPU
    },
    ModelTier.T2: {
        "name": "qwen2.5:3b",
        "context_length": 32000,
        "timeout_seconds": 90,
    },
    ModelTier.T3: {
        "name": "qwen2.5:0.5b",
        "context_length": 32000,
        "timeout_seconds": 30,  # Fast on CPU
    },
}

# Default to T3 for CPU-only operation
DEFAULT_TIER = ModelTier.T3


class OllamaClient:
    """
    Async Ollama client with 3-tier fallback.
    Falls back to smaller models on timeout/error.
    """
    
    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        default_tier: ModelTier = DEFAULT_TIER,
        enable_fallback: bool = True,
    ):
        self.base_url = base_url
        self.default_tier = default_tier
        self.enable_fallback = enable_fallback
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Lazy init async client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(300.0, connect=10.0),
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def health_check(self) -> dict:
        """Check if Ollama is running and which models are available."""
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            
            available_models = [m["name"] for m in data.get("models", [])]
            
            return {
                "status": "up",
                "available_models": available_models,
                "t1_available": any("phi4" in m for m in available_models),
                "t2_available": any("qwen2.5:3b" in m for m in available_models),
                "t3_available": any("qwen2.5:0.5b" in m for m in available_models),
            }
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return {"status": "down", "error": str(e)}
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tier: Optional[ModelTier] = None,
        temperature: float = 0.1,  # Low temp for factual responses
        max_tokens: int = 1024,
        json_mode: bool = False,
    ) -> LLMResponse:
        """
        Generate a response from Ollama.
        Uses fallback chain if primary model fails/times out.
        """
        tier = tier or self.default_tier
        fallback_chain = self._get_fallback_chain(tier)
        
        last_error = None
        for model_tier in fallback_chain:
            config = MODEL_CONFIG[model_tier]
            model_name = config["name"]
            timeout = config["timeout_seconds"]
            
            logger.info(f"Attempting generation with {model_name} (tier: {model_tier.name})")
            
            try:
                response = await self._call_ollama(
                    model=model_name,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout,
                    json_mode=json_mode,
                )
                
                if response.success:
                    response.model = model_tier.value
                    return response
                else:
                    last_error = response.error
                    logger.warning(f"{model_name} failed: {last_error}")
                    
            except asyncio.TimeoutError:
                last_error = f"Timeout after {timeout}s"
                logger.warning(f"{model_name} timed out")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"{model_name} error: {e}")
            
            if not self.enable_fallback:
                break
        
        # All tiers failed
        return LLMResponse(
            content="",
            model=tier.value,
            success=False,
            error=f"All model tiers failed. Last error: {last_error}",
        )
    
    async def _call_ollama(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        timeout: int,
        json_mode: bool,
    ) -> LLMResponse:
        """Make the actual API call to Ollama."""
        start_time = time.perf_counter()
        
        client = await self._get_client()
        
        # Build messages format (chat API)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        
        if json_mode:
            payload["format"] = "json"
        
        try:
            response = await asyncio.wait_for(
                client.post("/api/chat", json=payload),
                timeout=timeout,
            )
            response.raise_for_status()
            data = response.json()
            
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            content = data.get("message", {}).get("content", "")
            
            return LLMResponse(
                content=content,
                model=model,
                prompt_tokens=data.get("prompt_eval_count", 0),
                completion_tokens=data.get("eval_count", 0),
                latency_ms=latency_ms,
                success=True,
            )
            
        except httpx.HTTPStatusError as e:
            return LLMResponse(
                content="",
                model=model,
                success=False,
                error=f"HTTP {e.response.status_code}: {e.response.text}",
                latency_ms=(time.perf_counter() - start_time) * 1000,
            )
    
    def _get_fallback_chain(self, starting_tier: ModelTier) -> list[ModelTier]:
        """
        Get the fallback chain starting from a given tier.
        T1 -> T2 -> T3
        T2 -> T3
        T3 -> (no fallback)
        """
        all_tiers = [ModelTier.T1, ModelTier.T2, ModelTier.T3]
        start_idx = all_tiers.index(starting_tier)
        return all_tiers[start_idx:]


# Eagerly initialize to avoid race conditions during lazy initialization.
_client: OllamaClient = OllamaClient(default_tier=DEFAULT_TIER)


def get_ollama_client() -> OllamaClient:
    """Get the singleton Ollama client."""
    return _client


async def generate_completion(
    prompt: str,
    system_prompt: Optional[str] = None,
    json_mode: bool = False,
    tier: Optional[ModelTier] = None,
) -> LLMResponse:
    """Convenience function for quick generations."""
    client = get_ollama_client()
    return await client.generate(
        prompt=prompt,
        system_prompt=system_prompt,
        json_mode=json_mode,
        tier=tier,
    )
