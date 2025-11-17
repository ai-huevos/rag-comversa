"""
Multi-provider LLM client with automatic fallback
Integrates with existing rate limiter and model router
"""
import os
from typing import List, Dict, Optional
from .providers import (
    OpenAIProvider,
    AnthropicProvider,
    GeminiProvider,
    DeepSeekProvider,
    MoonshotProvider
)
from .model_router import MODEL_ROUTER
from .rate_limiter import get_rate_limiter
from .config import MODEL_PROVIDER_MAP


class MultiProviderClient:
    """
    Multi-provider LLM client with automatic model fallback
    Supports: OpenAI, Anthropic, Gemini, DeepSeek, Moonshot
    """

    def __init__(self):
        self.providers = self._initialize_providers()

    def _initialize_providers(self) -> Dict[str, any]:
        """Initialize all available providers"""
        providers = {}

        # OpenAI
        if os.getenv("OPENAI_API_KEY"):
            providers["openai"] = {
                "class": OpenAIProvider,
                "api_key": os.getenv("OPENAI_API_KEY")
            }

        # Anthropic
        if os.getenv("ANTHROPIC_API_KEY"):
            providers["anthropic"] = {
                "class": AnthropicProvider,
                "api_key": os.getenv("ANTHROPIC_API_KEY")
            }

        # Google Gemini
        if os.getenv("GEMINI_API_KEY"):
            providers["gemini"] = {
                "class": GeminiProvider,
                "api_key": os.getenv("GEMINI_API_KEY")
            }

        # DeepSeek
        if os.getenv("DEEPSEEK_API_KEY"):
            providers["deepseek"] = {
                "class": DeepSeekProvider,
                "api_key": os.getenv("DEEPSEEK_API_KEY")
            }

        # Moonshot
        if os.getenv("MOONSHOT_API_KEY"):
            providers["moonshot"] = {
                "class": MoonshotProvider,
                "api_key": os.getenv("MOONSHOT_API_KEY")
            }

        return providers

    def _get_provider(self, model: str):
        """Get provider instance for a model"""
        # Get provider name from config
        provider_name = MODEL_PROVIDER_MAP.get(model, {}).get("provider", "openai")

        if provider_name not in self.providers:
            raise ValueError(
                f"Provider '{provider_name}' not configured. "
                f"Please add {provider_name.upper()}_API_KEY to .env"
            )

        provider_class = self.providers[provider_name]["class"]
        api_key = self.providers[provider_name]["api_key"]

        return provider_class(api_key=api_key, model=model)

    def create_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4000,
        response_format: Optional[Dict] = None,
        initial_model: Optional[str] = None,
        max_retries: int = 3
    ) -> Optional[str]:
        """
        Create completion with automatic model fallback

        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            response_format: Optional response format (e.g., {"type": "json_object"})
            initial_model: Optional initial model (uses MODEL_ROUTER if None)
            max_retries: Max retries per model

        Returns:
            Completion text or None if all models fail
        """
        # Build model sequence
        model_sequence = MODEL_ROUTER.build_sequence(initial=initial_model)

        last_error = None

        for model in model_sequence:
            # Get provider for this model
            try:
                provider = self._get_provider(model)
            except ValueError as e:
                print(f"  ⚠️  {e}, skipping.")
                continue

            # Try this model with retries
            for attempt in range(max_retries):
                try:
                    print(f"  Attempting with model: {model} (attempt {attempt + 1}/{max_retries})")

                    # Rate limiting
                    rate_limit_key = provider.get_rate_limit_key()
                    limiter = get_rate_limiter(max_calls_per_minute=50, key=rate_limit_key)
                    limiter.wait_if_needed()

                    # Make API call
                    response = provider.create_completion(
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        response_format=response_format
                    )

                    print(f"  ✓ Success with {model}")
                    return response

                except Exception as e:
                    last_error = e
                    error_msg = str(e).lower()

                    # Check if rate limit error
                    if "rate" in error_msg or "quota" in error_msg or "limit" in error_msg:
                        print(f"  ⚠️  Rate limit hit on {model}, switching to next model")
                        break  # Switch to next model immediately

                    # Other errors - retry
                    print(f"  ❌ Error with {model} (attempt {attempt + 1}): {str(e)[:100]}")

                    if attempt < max_retries - 1:
                        print(f"  → Retrying with {model}...")
                    else:
                        print(f"  → Max retries reached for {model}, switching to next model")

        # All models failed
        print(f"  ❌ All models in fallback chain failed")
        if last_error:
            print(f"  Last error: {str(last_error)[:200]}")

        return None


# Global instance
multi_provider_client = MultiProviderClient()


def call_llm_with_fallback(
    messages: List[Dict[str, str]],
    temperature: float = 0.1,
    max_tokens: int = 4000,
    response_format: Optional[Dict] = None,
    max_retries: int = 3
) -> Optional[str]:
    """
    Convenience function for calling LLM with fallback

    Args:
        messages: List of message dicts
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        response_format: Optional response format
        max_retries: Max retries per model

    Returns:
        Completion text or None if all models fail
    """
    return multi_provider_client.create_completion(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=response_format,
        max_retries=max_retries
    )
