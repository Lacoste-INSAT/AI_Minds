"""
Ollama Client with 3-Tier Fallback
==================================
Tries models in order: phi4-mini → qwen2.5:3b → qwen2.5:0.5b

- T1 (phi4-mini): Best reasoning, 3.8B params, 2.5GB, 128K context
- T2 (qwen2.5:3b): Faster, 3.1B params, 1.9GB, 32K context  
- T3 (qwen2.5:0.5b): Low-resource fallback, 0.5B params, 398MB, 32K context

Air-gapped: all calls to localhost:11434 only.
"""

import httpx
import structlog
from dataclasses import dataclass
from enum import Enum
from typing import Optional, AsyncIterator
import asyncio
import json

logger = structlog.get_logger(__name__)


class ModelTier(Enum):
    """Model tiers in fallback order."""
    T1 = "phi4-mini"        # Best: phi4-mini-instruct
    T2 = "qwen2.5:3b"       # Fallback: qwen2.5-3b-instruct
    T3 = "qwen2.5:0.5b"     # Low-resource: qwen2.5-0.5b-instruct


# Tier configuration
TIER_CONFIG = {
    ModelTier.T1: {
        "model": "phi4-mini",
        "context_window": 128000,
        "timeout": 120.0,
        "description": "Phi-4-mini (3.8B) - best reasoning"
    },
    ModelTier.T2: {
        "model": "qwen2.5:3b", 
        "context_window": 32000,
        "timeout": 90.0,
        "description": "Qwen2.5-3B - balanced"
    },
    ModelTier.T3: {
        "model": "qwen2.5:0.5b",
        "context_window": 32000,
        "timeout": 60.0,
        "description": "Qwen2.5-0.5B - fast fallback"
    },
}


@dataclass
class LLMResponse:
    """Response from LLM call."""
    content: str
    model_used: str
    tier_used: ModelTier
    tokens_used: Optional[int] = None
    latency_ms: Optional[float] = None
    fallback_reason: Optional[str] = None


class OllamaClient:
    """
    Async Ollama client with 3-tier fallback.
    
    Usage:
        client = OllamaClient()
        response = await client.generate("Extract entities from this text...")
        print(f"Response from {response.model_used}: {response.content}")
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_tier: ModelTier = ModelTier.T1,
        enable_fallback: bool = True,
    ):
        self.base_url = base_url
        self.default_tier = default_tier
        self.enable_fallback = enable_fallback
        self._client: Optional[httpx.AsyncClient] = None
        self._available_models: set[str] = set()
        
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(180.0, connect=10.0)
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def check_health(self) -> bool:
        """Check if Ollama server is running."""
        try:
            client = await self._get_client()
            response = await client.get("/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.error("ollama_health_check_failed", error=str(e))
            return False
    
    async def list_models(self) -> list[str]:
        """List available models in Ollama."""
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            self._available_models = set(models)
            return models
        except Exception as e:
            logger.error("list_models_failed", error=str(e))
            return []
    
    async def is_model_available(self, model: str) -> bool:
        """Check if a specific model is available."""
        if not self._available_models:
            await self.list_models()
        # Check for exact match or model name without tag
        return (
            model in self._available_models or 
            any(m.startswith(model) for m in self._available_models)
        )
    
    async def pull_model(self, model: str) -> bool:
        """Pull a model from Ollama registry."""
        try:
            client = await self._get_client()
            logger.info("pulling_model", model=model)
            
            # Ollama pull is a streaming endpoint
            async with client.stream(
                "POST", 
                "/api/pull",
                json={"name": model},
                timeout=httpx.Timeout(600.0)  # 10 min timeout for large models
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            status = json.loads(line)
                            if "status" in status:
                                logger.debug("pull_progress", model=model, status=status["status"])
                        except json.JSONDecodeError:
                            pass
            
            # Refresh model list
            await self.list_models()
            logger.info("model_pulled", model=model)
            return True
            
        except Exception as e:
            logger.error("pull_model_failed", model=model, error=str(e))
            return False
    
    async def ensure_models_available(self) -> dict[ModelTier, bool]:
        """Ensure all tier models are available, pull if missing."""
        results = {}
        for tier in ModelTier:
            model = TIER_CONFIG[tier]["model"]
            available = await self.is_model_available(model)
            
            if not available:
                logger.info("model_not_found_pulling", model=model, tier=tier.name)
                available = await self.pull_model(model)
            
            results[tier] = available
            logger.info("model_status", tier=tier.name, model=model, available=available)
        
        return results
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tier: Optional[ModelTier] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> LLMResponse:
        """
        Generate completion with automatic fallback.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt for context/behavior
            tier: Starting tier (defaults to T1)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Max tokens to generate
            json_mode: Request JSON output format
            
        Returns:
            LLMResponse with content and metadata
        """
        start_tier = tier or self.default_tier
        tiers_to_try = self._get_fallback_chain(start_tier)
        
        last_error = None
        fallback_reason = None
        
        for current_tier in tiers_to_try:
            config = TIER_CONFIG[current_tier]
            model = config["model"]
            
            if not await self.is_model_available(model):
                logger.warning("model_unavailable_skipping", model=model, tier=current_tier.name)
                fallback_reason = f"{model} not available"
                continue
            
            try:
                import time
                start_time = time.perf_counter()
                
                response = await self._call_ollama(
                    model=model,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=config["timeout"],
                    json_mode=json_mode,
                )
                
                latency_ms = (time.perf_counter() - start_time) * 1000
                
                logger.info(
                    "llm_generation_success",
                    tier=current_tier.name,
                    model=model,
                    latency_ms=round(latency_ms, 2),
                    output_length=len(response.get("response", ""))
                )
                
                return LLMResponse(
                    content=response.get("response", ""),
                    model_used=model,
                    tier_used=current_tier,
                    tokens_used=response.get("eval_count"),
                    latency_ms=latency_ms,
                    fallback_reason=fallback_reason,
                )
                
            except asyncio.TimeoutError:
                last_error = f"Timeout after {config['timeout']}s"
                fallback_reason = f"{model} timed out"
                logger.warning("llm_timeout", model=model, tier=current_tier.name)
                
            except Exception as e:
                last_error = str(e)
                fallback_reason = f"{model} error: {str(e)[:50]}"
                logger.warning("llm_error", model=model, tier=current_tier.name, error=str(e))
            
            if not self.enable_fallback:
                break
        
        # All tiers failed
        logger.error("all_tiers_failed", last_error=last_error)
        raise RuntimeError(f"All LLM tiers failed. Last error: {last_error}")
    
    async def _call_ollama(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        timeout: float,
        json_mode: bool,
    ) -> dict:
        """Make the actual API call to Ollama."""
        client = await self._get_client()
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if json_mode:
            payload["format"] = "json"
        
        response = await client.post(
            "/api/generate",
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()
    
    async def chat(
        self,
        messages: list[dict[str, str]],
        tier: Optional[ModelTier] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> LLMResponse:
        """
        Chat completion with message history.
        
        Args:
            messages: List of {"role": "user"|"assistant"|"system", "content": "..."}
            tier: Starting tier
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            json_mode: Request JSON output format
            
        Returns:
            LLMResponse
        """
        start_tier = tier or self.default_tier
        tiers_to_try = self._get_fallback_chain(start_tier)
        
        last_error = None
        fallback_reason = None
        
        for current_tier in tiers_to_try:
            config = TIER_CONFIG[current_tier]
            model = config["model"]
            
            if not await self.is_model_available(model):
                fallback_reason = f"{model} not available"
                continue
            
            try:
                import time
                start_time = time.perf_counter()
                
                client = await self._get_client()
                
                payload = {
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    }
                }
                
                if json_mode:
                    payload["format"] = "json"
                
                response = await client.post(
                    "/api/chat",
                    json=payload,
                    timeout=config["timeout"],
                )
                response.raise_for_status()
                data = response.json()
                
                latency_ms = (time.perf_counter() - start_time) * 1000
                content = data.get("message", {}).get("content", "")
                
                logger.info(
                    "llm_chat_success",
                    tier=current_tier.name,
                    model=model,
                    latency_ms=round(latency_ms, 2)
                )
                
                return LLMResponse(
                    content=content,
                    model_used=model,
                    tier_used=current_tier,
                    tokens_used=data.get("eval_count"),
                    latency_ms=latency_ms,
                    fallback_reason=fallback_reason,
                )
                
            except asyncio.TimeoutError:
                last_error = f"Timeout"
                fallback_reason = f"{model} timed out"
                logger.warning("chat_timeout", model=model)
                
            except Exception as e:
                last_error = str(e)
                fallback_reason = f"{model} error"
                logger.warning("chat_error", model=model, error=str(e))
            
            if not self.enable_fallback:
                break
        
        raise RuntimeError(f"All LLM tiers failed. Last error: {last_error}")
    
    def _get_fallback_chain(self, start_tier: ModelTier) -> list[ModelTier]:
        """Get the fallback chain starting from a tier."""
        all_tiers = [ModelTier.T1, ModelTier.T2, ModelTier.T3]
        
        if not self.enable_fallback:
            return [start_tier]
        
        start_idx = all_tiers.index(start_tier)
        return all_tiers[start_idx:]


# Convenience functions for common operations
async def get_default_client() -> OllamaClient:
    """Get a default configured client."""
    client = OllamaClient()
    await client.list_models()  # Cache available models
    return client
