from unittest.mock import AsyncMock, patch
import pytest
from app.providers.mock_provider import MockProvider
from app.providers.deepseek_provider import DeepSeekProvider
from app.providers.together_provider import TogetherProvider
from app.providers.registry import provider_registry


@pytest.mark.asyncio
async def test_mock_provider_generate():
    provider = MockProvider()
    resp = await provider.generate("Write a quick Python sort function", model_id="mock-fast")
    assert resp.is_mock is True
    assert "DEMO/MOCK" in resp.content
    assert resp.input_tokens > 0
    assert resp.output_tokens > 0
    assert resp.provider_latency_ms > 0


@pytest.mark.asyncio
async def test_mock_provider_health():
    provider = MockProvider()
    health = await provider.check_health()
    assert health["status"] == "CONNECTED"
    assert "mock-fast" in health["models_available"]


@pytest.mark.asyncio
async def test_registry_contains_deepseek_and_together():
    deepseek = provider_registry.get_provider("deepseek")
    together = provider_registry.get_provider("together")
    assert deepseek is not None
    assert isinstance(deepseek, DeepSeekProvider)
    assert together is not None
    assert isinstance(together, TogetherProvider)


@pytest.mark.asyncio
async def test_deepseek_provider_unconfigured():
    provider = DeepSeekProvider(api_key=None)
    health = await provider.check_health()
    assert health["status"] == "NOT_CONFIGURED"

    resp = await provider.generate("Hello", model_id="deepseek-chat")
    assert resp.finish_reason == "error"
    assert "DEEPSEEK_API_KEY not configured" in resp.error


@pytest.mark.asyncio
async def test_together_provider_unconfigured():
    provider = TogetherProvider(api_key=None)
    health = await provider.check_health()
    assert health["status"] == "NOT_CONFIGURED"

    resp = await provider.generate("Hello", model_id="together-llama-3.3-70b")
    assert resp.finish_reason == "error"
    assert "TOGETHER_API_KEY not configured" in resp.error


@pytest.mark.asyncio
async def test_deepseek_provider_generate_success():
    provider = DeepSeekProvider(api_key="test-key")
    mock_json = {
        "choices": [{"message": {"content": "DeepSeek response"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
    }
    mock_resp = AsyncMock()
    mock_resp.raise_for_status = lambda: None
    mock_resp.json = lambda: mock_json

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        resp = await provider.generate("Hello", model_id="deepseek-chat")
        assert resp.content == "DeepSeek response"
        assert resp.provider == "deepseek"
        assert resp.model == "deepseek-chat"
        assert resp.input_tokens == 10
        assert resp.output_tokens == 20
        assert resp.total_tokens == 30


@pytest.mark.asyncio
async def test_together_provider_generate_success():
    provider = TogetherProvider(api_key="test-key")
    mock_json = {
        "choices": [{"message": {"content": "Together response"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 15, "completion_tokens": 25, "total_tokens": 40},
    }
    mock_resp = AsyncMock()
    mock_resp.raise_for_status = lambda: None
    mock_resp.json = lambda: mock_json

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        resp = await provider.generate("Hello", model_id="together-llama-3.3-70b")
        assert resp.content == "Together response"
        assert resp.provider == "together"
        assert resp.model == "together-llama-3.3-70b"
        assert resp.input_tokens == 15
        assert resp.output_tokens == 25
        assert resp.total_tokens == 40

