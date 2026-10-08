import sys
import os
import pytest
from unittest.mock import patch, MagicMock
import asyncio
from unittest.mock import AsyncMock

# Add sdk/python to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modelrouter import (
    ModelRouter,
    AsyncModelRouter,
    ChatMessage,
    ChatCompletion,
    RoutingDecision,
    AuthenticationError,
    RateLimitError,
)


def test_sdk_sync_chat():
    client = ModelRouter(api_key="test-key", base_url="http://127.0.0.1:8000")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "decision": {
            "decision_id": "dec-123",
            "request_id": "req-123",
            "selected_model": "mock-balanced",
            "selected_model_name": "Mock Balanced",
            "provider": "mock",
            "tier": "BALANCED",
            "confidence": 0.95,
            "policy_used": "balanced",
            "reasons": ["High quality"],
            "estimated_cost_usd": 0.0001,
            "estimated_latency_ms": 120.0,
        },
        "response": {
            "content": "Simulated output",
            "input_tokens": 10,
            "output_tokens": 20,
            "total_tokens": 30,
            "model": "mock-balanced",
        },
    }

    with patch("httpx.Client.post", return_value=mock_resp):
        res = client.chat.completions.create(prompt="Hello")
        assert res.model == "mock-balanced"
        assert res.choices[0].message.content == "Simulated output"


def test_async_client_context_returns_client_and_closes_on_exit():
    async def run():
        client = AsyncModelRouter(api_key="test-key")
        client.close = AsyncMock()
        async with client as entered:
            assert entered is client
            client.close.assert_not_awaited()
        client.close.assert_awaited_once_with()
    asyncio.run(run())


def test_async_client_context_closes_without_suppressing_errors():
    async def run():
        client = AsyncModelRouter(api_key="test-key")
        client.close = AsyncMock()
        with pytest.raises(ValueError, match="context failure"):
            async with client:
                raise ValueError("context failure")
        client.close.assert_awaited_once_with()
    asyncio.run(run())


def test_async_client_close_is_safe_to_repeat():
    async def run():
        client = AsyncModelRouter(api_key="test-key")
        await client.close()
        await client.close()
        async with client:
            pass
    asyncio.run(run())
