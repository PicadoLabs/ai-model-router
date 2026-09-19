import time
import httpx
from typing import AsyncGenerator, Dict, Any, Optional
from app.providers.base import ModelProvider
from app.models.schemas import ProviderResponse
from app.config.settings import get_settings

settings = get_settings()


class DeepSeekProvider(ModelProvider):
    """
    DeepSeek Provider Adapter (OpenAI-compatible chat completions).
    Uses DEEPSEEK_API_KEY from environment variables.
    """

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            provider_id="deepseek",
            name="DeepSeek",
            base_url="https://api.deepseek.com",
        )
        self.api_key = api_key or settings.DEEPSEEK_API_KEY

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
                error="DEEPSEEK_API_KEY not configured in environment.",
                is_mock=False,
                model=model_id,
                provider="deepseek",
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
                provider="deepseek",
            )
        except Exception as exc:
            return ProviderResponse(
                content="",
                finish_reason="error",
                error=f"DeepSeek error: {str(exc)}",
                is_mock=False,
                model=model_id,
                provider="deepseek",
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
            yield "[DeepSeek Error: API key not configured]"
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
        if max_tokens:
            payload["max_tokens"] = max_tokens

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
            yield f"\n[DeepSeek Streaming Error: {str(exc)}]"

    async def check_health(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"provider": "deepseek", "status": "NOT_CONFIGURED", "message": "API key not set in .env"}
        return {"provider": "deepseek", "status": "CONNECTED", "message": "API key configured."}
