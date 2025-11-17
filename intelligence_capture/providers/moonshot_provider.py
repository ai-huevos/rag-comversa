"""Moonshot AI provider implementation (OpenAI-compatible API)"""
from openai import OpenAI
from typing import List, Dict, Optional
from .base_provider import BaseLLMProvider


class MoonshotProvider(BaseLLMProvider):
    """Moonshot AI API provider (OpenAI-compatible)"""

    def __init__(self, api_key: str, model: str):
        super().__init__(api_key, model)
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.moonshot.cn/v1"
        )

    def create_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4000,
        response_format: Optional[Dict] = None
    ) -> str:
        """Create Moonshot completion"""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Moonshot supports response_format (OpenAI-compatible)
        if response_format:
            kwargs["response_format"] = response_format

        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    def get_rate_limit_key(self) -> str:
        return f"moonshot:{self.model}"
