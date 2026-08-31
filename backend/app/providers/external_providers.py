import time
import httpx
from typing import AsyncGenerator, Dict, Any, Optional
from app.providers.base import ModelProvider
from app.models.schemas import ProviderResponse
from app.config.settings import get_settings

settings = get_settings()


class OpenAIProvider(ModelProvider):
    """
    OpenAI Provider Adapter.
    Uses OPENAI_API_KEY from environment variables. Secrets are never exposed.
    """

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(provider_id="openai", name="OpenAI", base_url="https://api.openai.com/v1")
        self.api_key = api_key or settings.OPENAI_API_KEY

    async def generate(
        self,
        prompt: str,
        model_id: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> ProviderResponse:
        if not self.api_key:
            return ProviderResponse(
                content="",
                finish_reason="error",
                error="OPENAI_API_KEY not configured in environment.",
                is_mock=False,
                model=model_id,
                provider="openai",
            )

        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=settings.PROVIDER_TIMEOUT_SECONDS) as client:
                resp = await client.post(endpoint, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            choice = data["choices"][0]
            usage = data.get("usage", {})

            return ProviderResponse(
                content=choice["message"]["content"],
                finish_reason=choice.get("finish_reason", "stop"),
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                provider_latency_ms=round(elapsed_ms, 2),
                is_mock=False,
                model=model_id,
                provider="openai",
            )
        except Exception as exc:
            return ProviderResponse(
                content="",
                finish_reason="error",
                error=f"OpenAI error: {str(exc)}",
                is_mock=False,
                model=model_id,
                provider="openai",
                provider_latency_ms=(time.perf_counter() - start_time) * 1000.0,
            )

    async def stream(
        self,
        prompt: str,
        model_id: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            yield "[OpenAI Error: API key not configured]"
            return

        endpoint = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(timeout=settings.PROVIDER_TIMEOUT_SECONDS) as client:
                async with client.stream("POST", endpoint, json=payload, headers=headers) as resp:
                    async for line in resp.aiter_lines():
                        if line.startswith("data: ") and not line.endswith("[DONE]"):
                            import json
                            data = json.loads(line[6:])
                            delta = data["choices"][0].get("delta", {}).get("content", "")
                            if delta:
                                yield delta
        except Exception as exc:
            yield f"\n[OpenAI Streaming Error: {str(exc)}]"

    async def check_health(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"provider": "openai", "status": "NOT_CONFIGURED", "message": "API key not set in .env"}
        return {"provider": "openai", "status": "CONNECTED", "message": "API key configured."}


class AnthropicProvider(ModelProvider):
    """
    Anthropic Provider Adapter.
    """

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(provider_id="anthropic", name="Anthropic", base_url="https://api.anthropic.com/v1")
        self.api_key = api_key or settings.ANTHROPIC_API_KEY

    async def generate(
        self,
        prompt: str,
        model_id: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> ProviderResponse:
        if not self.api_key:
            return ProviderResponse(
                content="",
                finish_reason="error",
                error="ANTHROPIC_API_KEY not configured in environment.",
                is_mock=False,
                model=model_id,
                provider="anthropic",
            )

        endpoint = f"{self.base_url}/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens or 2048,
            "temperature": temperature,
        }
        if system_prompt:
            payload["system"] = system_prompt

        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=settings.PROVIDER_TIMEOUT_SECONDS) as client:
                resp = await client.post(endpoint, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            content = data["content"][0]["text"]
            usage = data.get("usage", {})

            return ProviderResponse(
                content=content,
                finish_reason=data.get("stop_reason", "stop"),
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                provider_latency_ms=round(elapsed_ms, 2),
                is_mock=False,
                model=model_id,
                provider="anthropic",
            )
        except Exception as exc:
            return ProviderResponse(
                content="",
                finish_reason="error",
                error=f"Anthropic error: {str(exc)}",
                is_mock=False,
                model=model_id,
                provider="anthropic",
                provider_latency_ms=(time.perf_counter() - start_time) * 1000.0,
            )

    async def stream(
        self,
        prompt: str,
        model_id: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        resp = await self.generate(prompt, model_id, system_prompt, temperature, max_tokens)
        if resp.error:
            yield f"[{resp.error}]"
            return
        for word in resp.content.split(" "):
            yield word + " "

    async def check_health(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"provider": "anthropic", "status": "NOT_CONFIGURED", "message": "API key not set in .env"}
        return {"provider": "anthropic", "status": "CONNECTED", "message": "API key configured."}


class GeminiProvider(ModelProvider):
    """
    Google Gemini Provider Adapter.
    """

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(provider_id="gemini", name="Google Gemini", base_url="https://generativelanguage.googleapis.com/v1beta")
        self.api_key = api_key or settings.GEMINI_API_KEY

    async def generate(
        self,
        prompt: str,
        model_id: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> ProviderResponse:
        if not self.api_key:
            return ProviderResponse(
                content="",
                finish_reason="error",
                error="GEMINI_API_KEY not configured in environment.",
                is_mock=False,
                model=model_id,
                provider="gemini",
            )

        endpoint = f"{self.base_url}/models/{model_id}:generateContent?key={self.api_key}"
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"System context: {system_prompt}"}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {"temperature": temperature},
        }

        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=settings.PROVIDER_TIMEOUT_SECONDS) as client:
                resp = await client.post(endpoint, json=payload)
                resp.raise_for_status()
                data = resp.json()

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            candidate = data["candidates"][0]
            text = candidate["content"]["parts"][0]["text"]
            usage = data.get("usageMetadata", {})

            return ProviderResponse(
                content=text,
                finish_reason=candidate.get("finishReason", "stop"),
                input_tokens=usage.get("promptTokenCount", 0),
                output_tokens=usage.get("candidatesTokenCount", 0),
                total_tokens=usage.get("totalTokenCount", 0),
                provider_latency_ms=round(elapsed_ms, 2),
                is_mock=False,
                model=model_id,
                provider="gemini",
            )
        except Exception as exc:
            return ProviderResponse(
                content="",
                finish_reason="error",
                error=f"Gemini error: {str(exc)}",
                is_mock=False,
                model=model_id,
                provider="gemini",
                provider_latency_ms=(time.perf_counter() - start_time) * 1000.0,
            )

    async def stream(
        self,
        prompt: str,
        model_id: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        resp = await self.generate(prompt, model_id, system_prompt, temperature, max_tokens)
        if resp.error:
            yield f"[{resp.error}]"
            return
        for word in resp.content.split(" "):
            yield word + " "

    async def check_health(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"provider": "gemini", "status": "NOT_CONFIGURED", "message": "API key not set in .env"}
        return {"provider": "gemini", "status": "CONNECTED", "message": "API key configured."}
