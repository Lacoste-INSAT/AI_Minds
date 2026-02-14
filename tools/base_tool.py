"""
Base Tool Class with Rate Limiting

Provides foundational infrastructure for all research tools with:
- Async HTTP client management
- Token bucket rate limiting
- Retry logic with exponential backoff
- Structured result format
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
import httpx

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """Standardized result from tool execution."""
    tool_name: str
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "tool_name": self.tool_name,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


class RateLimiter:
    """Token bucket rate limiter for API calls.
    
    Implements a simple token bucket algorithm to limit request rates.
    Tokens are replenished at a fixed rate up to a maximum capacity.
    """
    
    def __init__(self, requests_per_second: float = 1.0, burst_size: int = 3):
        """Initialize rate limiter.
        
        Args:
            requests_per_second: Rate at which tokens are replenished
            burst_size: Maximum number of tokens (allows short bursts)
        """
        self.rate = requests_per_second
        self.capacity = burst_size
        self.tokens = burst_size
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> float:
        """Acquire a token, waiting if necessary.
        
        Returns:
            Time waited in seconds
        """
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            
            # Replenish tokens based on elapsed time
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return 0.0
            
            # Calculate wait time
            wait_time = (1 - self.tokens) / self.rate
            self.tokens = 0
            
        # Wait outside the lock
        await asyncio.sleep(wait_time)
        
        async with self._lock:
            self.tokens = 0  # We consumed the token we waited for
            self.last_update = time.monotonic()
        
        return wait_time


class BaseTool(ABC):
    """Abstract base class for all research tools.
    
    Provides:
    - Async HTTP client management
    - Rate limiting
    - Retry logic with exponential backoff
    - Standardized result format
    """
    
    # Class-level rate limiters shared across instances of same tool type
    _rate_limiters: dict[str, RateLimiter] = {}
    
    def __init__(
        self,
        requests_per_second: float = 1.0,
        burst_size: int = 3,
        max_retries: int = 3,
        timeout: float = 30.0
    ):
        """Initialize base tool.
        
        Args:
            requests_per_second: Rate limit for this tool's API
            burst_size: Maximum burst requests allowed
            max_retries: Maximum retry attempts on failure
            timeout: HTTP request timeout in seconds
        """
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Create or reuse rate limiter for this tool type
        tool_name = self.__class__.__name__
        if tool_name not in BaseTool._rate_limiters:
            BaseTool._rate_limiters[tool_name] = RateLimiter(
                requests_per_second, burst_size
            )
        self._rate_limiter = BaseTool._rate_limiters[tool_name]
        
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this tool."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this tool does."""
        pass
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
                headers={"User-Agent": "CoScientist-Research-Agent/1.0"}
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        """Make HTTP request with rate limiting and retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional arguments for httpx request
            
        Returns:
            HTTP response
            
        Raises:
            httpx.HTTPError: If all retries fail
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            # Wait for rate limiter
            wait_time = await self._rate_limiter.acquire()
            if wait_time > 0:
                logger.debug(f"{self.name}: Rate limited, waited {wait_time:.2f}s")
            
            try:
                client = await self._get_client()
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response
                
            except httpx.HTTPStatusError as e:
                last_error = e
                status = e.response.status_code
                
                # Don't retry on client errors (except rate limit)
                if 400 <= status < 500 and status != 429:
                    logger.warning(f"{self.name}: Client error {status}, not retrying")
                    raise
                
                # Rate limit - wait longer
                if status == 429:
                    retry_after = int(e.response.headers.get("Retry-After", 60))
                    logger.warning(f"{self.name}: Rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    continue
                
                # Server error - retry with backoff
                delay = 2 ** attempt
                logger.warning(f"{self.name}: Server error {status}, retrying in {delay}s")
                await asyncio.sleep(delay)
                
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                delay = 2 ** attempt
                logger.warning(f"{self.name}: Connection error, retrying in {delay}s: {e}")
                await asyncio.sleep(delay)
        
        raise last_error or Exception(f"Request failed after {self.max_retries} attempts")
    
    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> ToolResult:
        """Search for information.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            ToolResult with search results
        """
        pass
    
    def _success_result(self, data: Any, **metadata) -> ToolResult:
        """Create a successful result."""
        return ToolResult(
            tool_name=self.name,
            success=True,
            data=data,
            metadata=metadata
        )
    
    def _error_result(self, error: str, **metadata) -> ToolResult:
        """Create an error result."""
        return ToolResult(
            tool_name=self.name,
            success=False,
            data=None,
            error=error,
            metadata=metadata
        )
