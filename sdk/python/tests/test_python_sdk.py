import sys
import os
import pytest
from unittest.mock import patch, MagicMock

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
