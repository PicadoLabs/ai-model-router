import time
import httpx
from typing import AsyncGenerator, Dict, Any, Optional
from app.providers.base import ModelProvider
from app.models.schemas import ProviderResponse
from app.config.settings import get_settings

settings = get_settings()


class OllamaProvider(ModelProvider):
    """
    Local Ollama Provider adapter.
    Executes real inference against locally running Ollama instance without external API keys.
    """

    def __init__(self, base_url: Optional[str] = None):
        url = base_url or settings.OLLAMA_BASE_URL
        super().__init__(provider_id="ollama", name="Ollama (Local)", base_url=url)

    def _strip_model_prefix(self, model_id: str) -> str:
        # e.g. "ollama-qwen2.5-coder" -> "qwen2.5-coder"
        if model_id.startswith("ollama-"):
            return model_id[len("ollama-"):]
        return model_id

    async def generate(
        self,
        prompt: str,
        model_id: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> ProviderResponse:
        real_model = self._strip_model_prefix(model_id)
        endpoint = f"{self.base_url.rstrip('/')}/api/generate"
        
        payload: Dict[str, Any] = {
            "model": real_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        if system_prompt:
            payload["system"] = system_prompt
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=settings.PROVIDER_TIMEOUT_SECONDS) as client:
                resp = await client.post(endpoint, json=payload)
                resp.raise_for_status()
                data = resp.json()
                
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            
            content = data.get("response", "")
            input_tokens = data.get("prompt_eval_count", max(1, len(prompt.split()) * 2))
            output_tokens = data.get("eval_count", max(1, len(content.split()) * 2))
            
            # Nanoseconds to ms if provided by ollama
            eval_duration_ms = data.get("eval_duration", 0) / 1_000_000.0 if "eval_duration" in data else elapsed_ms

            return ProviderResponse(
                content=content,
                finish_reason="stop" if data.get("done") else "length",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                provider_latency_ms=round(elapsed_ms, 2),
                time_to_first_token_ms=round(data.get("prompt_eval_duration", 0) / 1_000_000.0, 2) or None,
                is_mock=False,
                model=model_id,
                provider="ollama",
            )
        except Exception as exc:
            return ProviderResponse(
                content="",
                finish_reason="error",
                error=f"Ollama connection error ({str(exc)}). Is Ollama running on {self.base_url}?",
                is_mock=False,
                model=model_id,
                provider="ollama",
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
        real_model = self._strip_model_prefix(model_id)
        endpoint = f"{self.base_url.rstrip('/')}/api/generate"
        payload = {
            "model": real_model,
            "prompt": prompt,
            "stream": True,
            "options": {"temperature": temperature},
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=settings.PROVIDER_TIMEOUT_SECONDS) as client:
                async with client.stream("POST", endpoint, json=payload) as resp:
                    async for line in resp.aiter_lines():
                        if line:
                            import json
                            data = json.loads(line)
                            chunk = data.get("response", "")
                            if chunk:
                                yield chunk
        except Exception as exc:
            yield f"\n[Ollama Streaming Error: {str(exc)}]"

    async def check_health(self) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.base_url.rstrip('/')}/api/tags")
                if resp.status_code == 200:
                    models = [m.get("name") for m in resp.json().get("models", [])]
                    return {
                        "provider": "ollama",
                        "status": "CONNECTED",
                        "base_url": self.base_url,
                        "models_available": models,
                    }
        except Exception as exc:
            pass
        return {
            "provider": "ollama",
            "status": "NOT_CONNECTED",
            "base_url": self.base_url,
            "message": "Ollama service unreachable on configured port. Start via 'ollama serve'.",
        }
