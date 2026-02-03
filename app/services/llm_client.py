"""
LLM Client
OpenAI API wrapper with cost control.
"""

import json
from typing import Optional, Dict, Any

from openai import AsyncOpenAI

from app.core.config import settings
from app.utils.logger import log_llm_call


class LLMClient:
    """
    OpenAI API client.
    - Low temperature (0.3)
    - Strict JSON output
    - Cost tracking
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.temperature = settings.OPENAI_TEMPERATURE
        self.max_tokens = settings.OPENAI_MAX_TOKENS
    
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True
    ) -> Dict[str, Any]:
        """
        Generate response from LLM.
        Returns parsed JSON or raises exception.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        response_format = {"type": "json_object"} if json_mode else None
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format=response_format,
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            # Log the call
            log_llm_call(tokens_used, self.model)
            
            if json_mode:
                return {
                    "data": json.loads(content),
                    "tokens": tokens_used
                }
            else:
                return {
                    "data": content,
                    "tokens": tokens_used
                }
                
        except json.JSONDecodeError as e:
            raise LLMResponseError(f"Invalid JSON response: {e}")
        except Exception as e:
            raise LLMConnectionError(f"LLM call failed: {e}")
    
    async def generate_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3,
        validate_fn: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Generate with automatic retry on invalid format.
        """
        from app.core.constants import MAX_LLM_RETRIES, LLM_RETRY_DELAY_SECONDS
        import asyncio
        
        retries = min(max_retries, MAX_LLM_RETRIES)
        last_error = None
        
        for attempt in range(retries):
            try:
                result = await self.generate(system_prompt, user_prompt)
                
                # Validate if function provided
                if validate_fn:
                    is_valid, error = validate_fn(result["data"])
                    if not is_valid:
                        raise LLMResponseError(f"Validation failed: {error}")
                
                return result
                
            except (LLMResponseError, LLMConnectionError) as e:
                last_error = e
                if attempt < retries - 1:
                    await asyncio.sleep(LLM_RETRY_DELAY_SECONDS)
                continue
        
        raise last_error


class LLMResponseError(Exception):
    """Invalid LLM response."""
    pass


class LLMConnectionError(Exception):
    """LLM connection/API error."""
    pass


# Singleton instance
_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create LLM client instance."""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
