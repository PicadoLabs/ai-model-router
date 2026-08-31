import abc
import time
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional
from app.models.schemas import ProviderResponse


class ModelProvider(abc.ABC):
    """
    Abstract Base Class for all Model Providers (Mock, Ollama, OpenAI, Anthropic, Gemini, etc.)
    Ensures complete provider decoupling from routing logic.
    """

    def __init__(self, provider_id: str, name: str, base_url: Optional[str] = None):
        self.provider_id = provider_id
        self.name = name
        self.base_url = base_url

    @abc.abstractmethod
    async def generate(
        self,
        prompt: str,
        model_id: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> ProviderResponse:
        """Execute a text generation call against the model provider."""
        pass

    @abc.abstractmethod
    async def stream(
        self,
        prompt: str,
        model_id: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream generated response chunks."""
        pass

    @abc.abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """Check provider connectivity, status, and loaded models."""
        pass
