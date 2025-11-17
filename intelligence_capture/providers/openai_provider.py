"""OpenAI provider implementation"""
from openai import OpenAI
from typing import List, Dict, Optional
from .base_provider import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider"""

    def __init__(self, api_key: str, model: str):
        super().__init__(api_key, model)
        self.client = OpenAI(api_key=api_key)

    def create_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4000,
        response_format: Optional[Dict] = None
    ) -> str:
        """Create OpenAI completion"""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            kwargs["response_format"] = response_format

        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    def get_rate_limit_key(self) -> str:
        return f"openai:{self.model}"
