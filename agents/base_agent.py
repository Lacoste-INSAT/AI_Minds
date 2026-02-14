import json
import logging
import re
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AsyncIterator, Any, Optional

from prompts.loader import load_prompt
from providers import factory

logger = logging.getLogger(__name__)


# Configuration for retry logic
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # seconds
RETRY_BACKOFF = 2.0  # exponential backoff multiplier


@dataclass
class AgentResult:
    name: str
    output: dict
    confidence: float
    timestamp: str


class BaseAgent:
    name = "base"

    async def run(self, state: dict) -> AgentResult:
        raise NotImplementedError

    async def _ask(self, prompt_name: str, state: dict, max_retries: int = MAX_RETRIES) -> dict:
        """Ask the LLM and return parsed JSON content with retry logic.
        
        Args:
            prompt_name: Name of the prompt template
            state: Input state dictionary
            max_retries: Maximum number of retry attempts
        
        Returns:
            dict: Parsed JSON response from the LLM
            
        Raises:
            ValueError: If response cannot be parsed after all retries
        """
        provider = factory.get_provider()
        prompt = load_prompt(prompt_name)
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps(state, indent=2)},
        ]
        
        last_error = None
        for attempt in range(max_retries):
            try:
                logger.info(f"LLM request attempt {attempt + 1}/{max_retries} for {prompt_name}")
                raw_response = await provider.generate(messages)
                parsed = self._parse_llm_response(raw_response, prompt_name)
                
                # Validate the response if schema validation is available
                validated = self._validate_response(parsed, prompt_name)
                
                logger.info(f"Successfully parsed response for {prompt_name}")
                return validated
                
            except ValueError as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed for {prompt_name}: {e}")
                
                if attempt < max_retries - 1:
                    # Calculate backoff delay
                    delay = RETRY_DELAY * (RETRY_BACKOFF ** attempt)
                    logger.info(f"Retrying after {delay:.1f}s...")
                    await asyncio.sleep(delay)
                    
                    # Add helpful context to the prompt for retry
                    messages.append({
                        "role": "assistant",
                        "content": "I apologize, my previous response had formatting issues."
                    })
                    messages.append({
                        "role": "user",
                        "content": "Please provide a valid JSON response following the exact schema specified."
                    })
                else:
                    logger.error(f"All {max_retries} attempts failed for {prompt_name}")
            
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error in attempt {attempt + 1}: {e}", exc_info=True)
                if attempt < max_retries - 1:
                    delay = RETRY_DELAY * (RETRY_BACKOFF ** attempt)
                    await asyncio.sleep(delay)
        
        # If we get here, all retries failed
        raise ValueError(f"Failed to get valid response after {max_retries} attempts: {last_error}")
    
    def _validate_response(self, parsed: dict, context: str) -> dict:
        """Validate parsed response against expected schema.
        
        Args:
            parsed: Parsed dictionary from LLM
            context: Context for logging
            
        Returns:
            Validated dictionary (potentially cleaned/normalized)
        """
        # Optional: Add schema validation here
        # For now, just do basic sanity checks
        
        if not isinstance(parsed, dict):
            raise ValueError(f"Response must be a dictionary, got {type(parsed)}")
        
        if not parsed:
            raise ValueError("Response dictionary is empty")
        
        logger.debug(f"Response validation passed for {context}")
        return parsed
    
    async def _ask_stream(self, prompt_name: str, state: dict) -> AsyncIterator[str]:
        """Stream tokens from LLM in real-time."""
        provider = factory.get_provider()
        prompt = load_prompt(prompt_name)
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps(state, indent=2)},
        ]
        async for chunk in provider.stream(messages):
            yield chunk

    async def run_stream(self, state: dict) -> AsyncIterator[str]:
        """Stream the agent's response token by token.
        
        Override in subclasses to provide streaming behavior.
        Default implementation falls back to non-streaming.
        """
        result = await self.run(state)
        yield json.dumps(result.output, indent=2)

    def _parse_llm_response(self, response: dict, context: str = "") -> dict:
        """Extract and parse JSON content from LLM API response.
        
        Args:
            response: Raw API response from LLM provider
            context: Context string for error messages
            
        Returns:
            Parsed JSON object from the assistant's message
            
        Raises:
            ValueError: If response contains errors or cannot be parsed
        """
        # Check for API errors
        if "error" in response:
            error_info = response["error"]
            if isinstance(error_info, dict):
                status = error_info.get("status_code", "unknown")
                message = error_info.get("body", str(error_info))
            else:
                status = "unknown"
                message = str(error_info)
            raise ValueError(f"LLM API error [{status}]: {message}")
        
        # Extract content from LLM response format
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Unexpected response format in {context}: {response}")
            raise ValueError(f"Invalid response structure: {e}")
        
        if not content or not isinstance(content, str):
            raise ValueError(f"Empty or invalid content from LLM in {context}")
        
        # Parse JSON from content
        return self._extract_json(content, context)
    
    def _extract_json(self, content: str, context: str = "") -> dict:
        """Extract and parse JSON from LLM text response.
        
        Handles various formats:
        - Plain JSON
        - JSON wrapped in markdown code blocks
        - JSON with surrounding text
        
        Args:
            content: Text content from LLM
            context: Context for error messages
            
        Returns:
            Parsed JSON object
            
        Raises:
            ValueError: If JSON cannot be extracted or parsed
        """
        content = content.strip()
        
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\\s*({.*?})\\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        else:
            # Try to find JSON object boundaries
            if '{' in content and '}' in content:
                start = content.find('{')
                # Find matching closing brace
                end = content.rfind('}') + 1
                content = content[start:end]
        
        # Attempt to parse JSON
        try:
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise ValueError(f"Expected JSON object, got {type(parsed).__name__}")
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in {context}: {e}")
            logger.debug(f"Content that failed to parse: {content[:500]}...")
            raise ValueError(f"Failed to parse JSON from LLM response: {e}")

    def _result(self, output: dict, confidence: float) -> AgentResult:
        ts = datetime.now(timezone.utc).isoformat()
        return AgentResult(self.name, output, confidence, ts)
