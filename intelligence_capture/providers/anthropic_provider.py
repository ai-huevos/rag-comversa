"""Anthropic Claude provider implementation"""
from anthropic import Anthropic
from typing import List, Dict, Optional
import json
from .base_provider import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API provider"""

    def __init__(self, api_key: str, model: str):
        super().__init__(api_key, model)
        self.client = Anthropic(api_key=api_key)

    def create_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4000,
        response_format: Optional[Dict] = None
    ) -> str:
        """Create Claude completion"""
        # Anthropic requires system message separate
        system_message = None
        conversation_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                conversation_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # Add JSON format instruction if requested
        if response_format and response_format.get("type") == "json_object":
            if conversation_messages:
                conversation_messages[-1]["content"] += "\n\nRespond with valid JSON only."

        kwargs = {
            "model": self.model,
            "messages": conversation_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if system_message:
            kwargs["system"] = system_message

        response = self.client.messages.create(**kwargs)
        return response.content[0].text

    def get_rate_limit_key(self) -> str:
        return f"anthropic:{self.model}"
