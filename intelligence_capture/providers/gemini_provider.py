"""Google Gemini provider implementation"""
import google.generativeai as genai
from typing import List, Dict, Optional
import json
from .base_provider import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider"""

    def __init__(self, api_key: str, model: str):
        super().__init__(api_key, model)
        genai.configure(api_key=api_key)

        # Configure generation settings
        self.generation_config = {
            "temperature": 0.1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 4000,
        }

    def create_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4000,
        response_format: Optional[Dict] = None
    ) -> str:
        """Create Gemini completion"""
        # Update generation config
        self.generation_config["temperature"] = temperature
        self.generation_config["max_output_tokens"] = max_tokens

        # Add JSON format instruction if requested
        if response_format and response_format.get("type") == "json_object":
            self.generation_config["response_mime_type"] = "application/json"

        model = genai.GenerativeModel(
            model_name=self.model,
            generation_config=self.generation_config
        )

        # Convert messages to Gemini format
        # Gemini uses a different message format
        history = []
        user_message = None

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                # Add system message as first user message
                history.append({
                    "role": "user",
                    "parts": [content]
                })
                history.append({
                    "role": "model",
                    "parts": ["Understood. I will follow these instructions."]
                })
            elif role == "user":
                user_message = content
            elif role == "assistant":
                if user_message:
                    history.append({
                        "role": "user",
                        "parts": [user_message]
                    })
                    user_message = None
                history.append({
                    "role": "model",
                    "parts": [content]
                })

        # Start chat with history
        chat = model.start_chat(history=history if history else None)

        # Send final user message
        if user_message is None and messages:
            user_message = messages[-1]["content"]

        response = chat.send_message(user_message)
        return response.text

    def get_rate_limit_key(self) -> str:
        return f"gemini:{self.model}"
