import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Add sdk/python to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "sdk", "python")))

from modelrouter import (
    ModelRouter,
    AsyncModelRouter,
    ChatMessage,
    ChatCompletion,
    RoutingDecision,
    AuthenticationError,
    RateLimitError,
    APIStatusError,
    APIConnectionError,
)


def test_sdk_sync_chat_completion():
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
            "reasons": ["High quality score"],
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
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hello router!"}]
        )
        assert isinstance(res, ChatCompletion)
        assert res.model == "mock-balanced"
        assert res.choices[0].message.content == "Simulated output"
        assert res.usage.total_tokens == 30


def test_sdk_sync_route_dryrun():
    client = ModelRouter(base_url="http://127.0.0.1:8000")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "decision_id": "dec-456",
        "request_id": "req-456",
        "selected_model": "mock-fast",
        "selected_model_name": "Mock Fast",
        "provider": "mock",
        "tier": "FAST",
        "confidence": 0.88,
        "policy_used": "cost_optimized",
        "reasons": ["Cost efficiency"],
        "estimated_cost_usd": 0.0,
        "estimated_latency_ms": 50.0,
    }

    with patch("httpx.Client.post", return_value=mock_resp):
        decision = client.route(prompt="Quick query", policy="cost_optimized")
        assert isinstance(decision, RoutingDecision)
        assert decision.selected_model == "mock-fast"
        assert decision.confidence == 0.88


def test_sdk_error_handling():
    client = ModelRouter(base_url="http://127.0.0.1:8000")

    # 401 Auth error
    mock_401 = MagicMock()
    mock_401.status_code = 401
    mock_401.text = '{"detail": "Invalid API key"}'
    with patch("httpx.Client.post", return_value=mock_401):
        with pytest.raises(AuthenticationError):
            client.chat.completions.create(prompt="test")

    # 429 Rate limit error
    mock_429 = MagicMock()
    mock_429.status_code = 429
    mock_429.text = '{"detail": "Workspace rate limit exceeded"}'
    with patch("httpx.Client.post", return_value=mock_429):
        with pytest.raises(RateLimitError):
            client.chat.completions.create(prompt="test")


@pytest.mark.asyncio
async def test_sdk_async_chat_completion():
    client = AsyncModelRouter(base_url="http://127.0.0.1:8000")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "decision": {
            "decision_id": "dec-789",
            "request_id": "req-789",
            "selected_model": "mock-power",
            "selected_model_name": "Mock Power",
            "provider": "mock",
            "tier": "POWER",
            "confidence": 0.99,
            "policy_used": "quality_first",
            "reasons": ["Complex reasoning task"],
            "estimated_cost_usd": 0.002,
            "estimated_latency_ms": 300.0,
        },
        "response": {
            "content": "Async simulated output",
            "input_tokens": 15,
            "output_tokens": 25,
            "total_tokens": 40,
            "model": "mock-power",
        },
    }

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        res = await client.chat.complete(prompt="Complex math proof")
        assert res.model == "mock-power"
        assert res.choices[0].message.content == "Async simulated output"
