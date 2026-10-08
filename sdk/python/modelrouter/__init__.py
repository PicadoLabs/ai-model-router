"""
Model Router Python SDK: Lightweight, drop-in intelligent routing client for AI models.
"""

from modelrouter.client import ModelRouter, AsyncModelRouter
from modelrouter.exceptions import (
    ModelRouterError,
    AuthenticationError,
    RateLimitError,
    APIConnectionError,
    APIStatusError,
    RoutingError,
)
from modelrouter.types import (
    ChatMessage,
    ChatCompletion,
    ChatCompletionChunk,
    RoutingDecision,
    ModelInfo,
    Usage,
)

__version__ = "0.2.0"

__all__ = [
    "ModelRouter",
    "AsyncModelRouter",
    "ModelRouterError",
    "AuthenticationError",
    "RateLimitError",
    "APIConnectionError",
    "APIStatusError",
    "RoutingError",
    "ChatMessage",
    "ChatCompletion",
    "ChatCompletionChunk",
    "RoutingDecision",
    "ModelInfo",
    "Usage",
]
