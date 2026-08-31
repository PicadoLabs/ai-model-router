import asyncio
import time
from typing import AsyncGenerator, Dict, Any, Optional
from app.providers.base import ModelProvider
from app.models.schemas import ProviderResponse


class MockProvider(ModelProvider):
    """
    Mock Provider for development, testing, and zero-cost simulation.
    All outputs are explicitly labeled as DEMO/MOCK.
    """

    def __init__(self):
        super().__init__(provider_id="mock", name="Mock / Demo Provider")

    async def generate(
        self,
        prompt: str,
        model_id: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> ProviderResponse:
        start_time = time.perf_counter()
        
        # Simulate realistic latency based on tier
        tier_delay = 0.08 if "fast" in model_id else (0.18 if "balanced" in model_id else 0.35)
        await asyncio.sleep(tier_delay)
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        
        # Calculate realistic token estimations
        input_tokens = max(1, len(prompt.split()) * 2)
        
        # Response tailored to task keywords
        prompt_lower = prompt.lower()
        if "python" in prompt_lower or "code" in prompt_lower or "def " in prompt_lower or "function" in prompt_lower:
            content = (
                f"[DEMO/MOCK RESPONSE from {model_id}]\n\n"
                f"```python\n"
                f"# Mock implementation generated for: {prompt[:60]}...\n"
                f"def solve_problem(*args, **kwargs):\n"
                f"    \"\"\"Simulated response from Model Router Demo Engine.\"\"\"\n"
                f"    result = [x for x in args if x is not None]\n"
                f"    return {{'status': 'success', 'data': result, 'model': '{model_id}'}}\n"
                f"```\n\n"
                f"This code was returned by the simulated {model_id} engine."
            )
        elif "debug" in prompt_lower or "error" in prompt_lower or "bug" in prompt_lower:
            content = (
                f"[DEMO/MOCK RESPONSE from {model_id}]\n\n"
                f"### Root Cause Analysis:\n"
                f"1. **Potential Bottleneck**: Asynchronous task scheduling without proper semaphore limits.\n"
                f"2. **Mitigation**: Introduce bounded concurrency worker pools.\n"
                f"3. **Verification**: Checked against {model_id} simulated reasoning engine."
            )
        elif "summary" in prompt_lower or "summarize" in prompt_lower:
            content = (
                f"[DEMO/MOCK RESPONSE from {model_id}]\n\n"
                f"**Executive Summary**:\n"
                f"• Main point: {prompt[:80]}...\n"
                f"• Key takeaway: High routing accuracy achieved with minimal latency overhead."
            )
        else:
            content = (
                f"[DEMO/MOCK RESPONSE from {model_id}]\n\n"
                f"Processed request: \"{prompt[:100]}\"\n\n"
                f"This is a simulated response generated locally by Model Router Mock Engine without external API calls."
            )

        output_tokens = max(1, len(content.split()) * 2)
        total_tokens = input_tokens + output_tokens

        return ProviderResponse(
            content=content,
            finish_reason="stop",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            provider_latency_ms=round(elapsed_ms, 2),
            time_to_first_token_ms=round(tier_delay * 500, 2),
            is_mock=True,
            model=model_id,
            provider="mock",
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
        chunks = resp.content.split(" ")
        for chunk in chunks:
            await asyncio.sleep(0.02)
            yield chunk + " "

    async def check_health(self) -> Dict[str, Any]:
        return {
            "provider": "mock",
            "status": "CONNECTED",
            "message": "Mock provider active (Demo Mode). Zero API keys required.",
            "models_available": ["mock-fast", "mock-balanced", "mock-power"],
        }
