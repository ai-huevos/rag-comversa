"""
Base class for LLM providers
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseLLMProvider(ABC):
    """Base class for all LLM providers"""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    @abstractmethod
    def create_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4000,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        Create a chat completion

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            response_format: Optional response format specification

        Returns:
            The completion text

        Raises:
            Exception: If the API call fails
        """
        pass

    @abstractmethod
    def get_rate_limit_key(self) -> str:
        """Get the rate limiter key for this provider"""
        pass
