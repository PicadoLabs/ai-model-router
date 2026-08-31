import time
import asyncio
from typing import List, Optional, Tuple, Dict, Any
from app.models.schemas import ProviderResponse, ModelMetadata
from app.providers.registry import provider_registry
from app.config.settings import get_settings

settings = get_settings()

RETRYABLE_ERRORS = [
    "timeout",
    "connection error",
    "rate limit",
    "429",
    "503",
    "service unavailable",
    "econnreset",
]


def is_retryable(error_str: Optional[str]) -> bool:
    if not error_str:
        return False
    low = error_str.lower()
    return any(keyword in low for keyword in RETRYABLE_ERRORS)


async def execute_with_fallback(
    prompt: str,
    selected_model_id: str,
    selected_provider_id: str,
    all_models: List[ModelMetadata],
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_retries: int = 1,
) -> Tuple[ProviderResponse, bool, Optional[str], Optional[str]]:
    """
    Executes model generation with configurable retries and fallback hierarchy.
    Returns: (ProviderResponse, fallback_used, original_model, fallback_reason)
    """
    current_model_id = selected_model_id
    current_provider_id = selected_provider_id
    fallback_used = False
    original_model = selected_model_id
    fallback_reason = None

    # Step 1: Attempt primary model with retries
    provider = provider_registry.get_provider(current_provider_id)
    if not provider:
        provider = provider_registry.get_provider("mock")
        current_provider_id = "mock"
        current_model_id = "mock-balanced"
        fallback_used = True
        fallback_reason = f"Provider '{selected_provider_id}' is not loaded. Fell back to Mock."

    for attempt in range(max_retries + 1):
        resp = await provider.generate(
            prompt=prompt,
            model_id=current_model_id,
            system_prompt=system_prompt,
            temperature=temperature,
        )

        if not resp.error and resp.finish_reason != "error":
            return resp, fallback_used, original_model if fallback_used else None, fallback_reason

        # If non-retryable error or last attempt, prepare for fallback
        if not is_retryable(resp.error) or attempt == max_retries:
            fallback_reason = resp.error or "Unknown primary model execution error."
            break

        await asyncio.sleep(0.5 * (attempt + 1))

    # Step 2: Determine Fallback Candidate
    fallback_used = True
    # Priority: Mock model of same or balanced tier, or active local Ollama
    candidate_fallbacks = [
        m for m in all_models
        if m.id != selected_model_id and m.is_active and (m.provider == "mock" or m.type == "LOCAL")
    ]
    if not candidate_fallbacks:
        candidate_fallbacks = [m for m in all_models if m.id != selected_model_id and m.is_active]

    fallback_target = candidate_fallbacks[0] if candidate_fallbacks else None

    if fallback_target:
        fb_provider = provider_registry.get_provider(fallback_target.provider) or provider_registry.get_provider("mock")
        fb_resp = await fb_provider.generate(
            prompt=prompt,
            model_id=fallback_target.id,
            system_prompt=system_prompt,
            temperature=temperature,
        )
        if not fb_resp.error:
            return fb_resp, True, original_model, f"Primary model failed: {fallback_reason} -> Fallback to {fallback_target.id}"

    # Step 3: Emergency Hard Mock fallback
    emergency_mock = provider_registry.get_provider("mock")
    emergency_resp = await emergency_mock.generate(
        prompt=prompt,
        model_id="mock-balanced",
        system_prompt=system_prompt,
        temperature=temperature,
    )
    return emergency_resp, True, original_model, f"Emergency fallback triggered due to: {fallback_reason}"
