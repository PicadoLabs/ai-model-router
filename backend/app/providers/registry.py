from typing import Dict, Optional
from app.providers.base import ModelProvider
from app.providers.mock_provider import MockProvider
from app.providers.ollama_provider import OllamaProvider
from app.providers.external_providers import OpenAIProvider, AnthropicProvider, GeminiProvider
from app.config.settings import get_settings

settings = get_settings()


class ProviderRegistry:
    """
    Central registry managing provider instances.
    """

    def __init__(self):
        self._providers: Dict[str, ModelProvider] = {
            "mock": MockProvider(),
            "ollama": OllamaProvider(base_url=settings.OLLAMA_BASE_URL),
            "openai": OpenAIProvider(api_key=settings.OPENAI_API_KEY),
            "anthropic": AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY),
            "gemini": GeminiProvider(api_key=settings.GEMINI_API_KEY),
        }

    def get_provider(self, provider_id: str) -> Optional[ModelProvider]:
        return self._providers.get(provider_id.lower())

    def register_provider(self, provider_id: str, provider: ModelProvider):
        self._providers[provider_id.lower()] = provider

    def list_providers(self) -> Dict[str, ModelProvider]:
        return self._providers


provider_registry = ProviderRegistry()
