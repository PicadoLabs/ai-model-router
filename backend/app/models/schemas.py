from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TaskType(str, Enum):
    GENERAL_QA = "GENERAL_QA"
    CODING = "CODING"
    DEBUGGING = "DEBUGGING"
    REASONING = "REASONING"
    SUMMARIZATION = "SUMMARIZATION"
    EXTRACTION = "EXTRACTION"
    WRITING = "WRITING"
    TRANSLATION = "TRANSLATION"
    ANALYSIS = "ANALYSIS"
    MATH = "MATH"
    LONG_CONTEXT = "LONG_CONTEXT"
    CREATIVE = "CREATIVE"


class PriorityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ModelTier(str, Enum):
    FAST = "FAST"
    BALANCED = "BALANCED"
    POWER = "POWER"


class ProviderType(str, Enum):
    MOCK = "mock"
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    CUSTOM = "custom"


class RequestAnalysis(BaseModel):
    task_type: TaskType = Field(default=TaskType.GENERAL_QA)
    complexity: float = Field(default=0.5, ge=0.0, le=1.0)
    complexity_label: PriorityLevel = Field(default=PriorityLevel.MEDIUM)
    reasoning_required: bool = Field(default=False)
    coding_required: bool = Field(default=False)
    vision_required: bool = Field(default=False)
    tools_required: bool = Field(default=False)
    context_size: int = Field(default=0)  # in estimated tokens / characters
    latency_priority: PriorityLevel = Field(default=PriorityLevel.MEDIUM)
    cost_sensitivity: PriorityLevel = Field(default=PriorityLevel.MEDIUM)
    quality_requirement: PriorityLevel = Field(default=PriorityLevel.MEDIUM)
    keywords_detected: List[str] = Field(default_factory=list)
    analyzer_used: str = Field(default="rules")


class ModelMetadata(BaseModel):
    id: str
    name: str
    provider: str
    type: str = "LOCAL"  # LOCAL, CLOUD, MOCK
    tier: ModelTier = ModelTier.BALANCED
    context_window: int = 8192
    
    supports_coding: bool = False
    supports_reasoning: bool = False
    supports_vision: bool = False
    supports_tools: bool = False
    
    quality_score: float = 0.75  # 0.0 - 1.0
    speed_score: float = 0.75    # 0.0 - 1.0
    reliability_score: float = 0.95
    
    cost_per_input_token: float = 0.0
    cost_per_output_token: float = 0.0
    availability: str = "AVAILABLE"
    is_active: bool = True


class CandidateScore(BaseModel):
    model_id: str
    model_name: str
    provider: str
    tier: str
    overall_score: float  # 0 - 100
    quality_component: float
    cost_component: float
    speed_component: float
    capability_component: float
    reliability_component: float
    estimated_latency_ms: float
    estimated_cost_usd: float
    eligible: bool = True
    rejection_reason: Optional[str] = None


class RoutingDecision(BaseModel):
    decision_id: str
    request_id: str
    selected_model: str
    selected_model_name: str
    provider: str
    tier: str
    confidence: float
    policy_used: str
    reasons: List[str]
    candidate_scores: List[CandidateScore]
    rejected_candidates: Dict[str, str] = Field(default_factory=dict)
    estimated_cost_usd: float
    estimated_latency_ms: float
    rule_applied: Optional[str] = None
    timestamp: str


class ProviderResponse(BaseModel):
    content: str
    finish_reason: str = "stop"
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    provider_latency_ms: float = 0.0
    time_to_first_token_ms: Optional[float] = None
    is_mock: bool = False
    model: str = ""
    provider: str = ""
    error: Optional[str] = None
