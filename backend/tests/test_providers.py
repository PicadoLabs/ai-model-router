import pytest
from app.providers.mock_provider import MockProvider


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
