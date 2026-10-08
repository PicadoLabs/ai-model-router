from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = "user"  # system, user, assistant
    content: str


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: Optional[float] = None


class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: Optional[str] = "stop"


class ChatCompletion(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Usage
    routing_metadata: Optional[Dict[str, Any]] = None


class ChatCompletionChunkDelta(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None


class ChatCompletionChunkChoice(BaseModel):
    index: int = 0
    delta: ChatCompletionChunkDelta
    finish_reason: Optional[str] = None


class ChatCompletionChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatCompletionChunkChoice]
    routing_metadata: Optional[Dict[str, Any]] = None


class RoutingDecision(BaseModel):
    decision_id: str
    request_id: str
    selected_model: str
    selected_model_name: str
    provider: str
    tier: str
    confidence: float
    policy_used: str
    reasons: List[str] = Field(default_factory=list)
    estimated_cost_usd: float
    estimated_latency_ms: float
    rejected_candidates: Dict[str, str] = Field(default_factory=dict)
    rule_applied: Optional[str] = None


class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    tier: str
    context_window: int
    quality_score: float
    speed_score: float
    cost_per_input_token: float
    cost_per_output_token: float
    is_active: bool = True
