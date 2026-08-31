import datetime
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    Text,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class ModelRecord(Base):
    __tablename__ = "models"

    id = Column(String(100), primary_key=True)
    name = Column(String(200), nullable=False)
    provider = Column(String(50), nullable=False)  # mock, ollama, openai, anthropic, gemini
    type = Column(String(50), default="LOCAL")  # LOCAL, CLOUD, MOCK
    context_window = Column(Integer, default=8192)
    
    supports_coding = Column(Boolean, default=False)
    supports_reasoning = Column(Boolean, default=False)
    supports_vision = Column(Boolean, default=False)
    supports_tools = Column(Boolean, default=False)
    
    quality_score = Column(Float, default=0.7)
    speed_score = Column(Float, default=0.7)
    reliability_score = Column(Float, default=0.95)
    
    cost_per_input_token = Column(Float, default=0.0)
    cost_per_output_token = Column(Float, default=0.0)
    
    availability = Column(String(50), default="AVAILABLE")
    is_active = Column(Boolean, default=True)
    tier = Column(String(50), default="BALANCED")  # FAST, BALANCED, POWER
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class ProviderRecord(Base):
    __tablename__ = "providers"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    status = Column(String(50), default="READY")  # READY, CONNECTED, NOT_CONFIGURED, ERROR
    is_enabled = Column(Boolean, default=True)
    base_url = Column(String(500), nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class RoutingPolicyRecord(Base):
    __tablename__ = "routing_policies"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    quality_weight = Column(Float, default=0.35)
    cost_weight = Column(Float, default=0.25)
    speed_weight = Column(Float, default=0.20)
    capability_weight = Column(Float, default=0.15)
    reliability_weight = Column(Float, default=0.05)
    is_default = Column(Boolean, default=False)


class RoutingRuleRecord(Base):
    __tablename__ = "routing_rules"

    id = Column(String(100), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    priority = Column(Integer, default=0)
    is_enabled = Column(Boolean, default=True)
    
    condition_field = Column(String(100), nullable=False)  # task_type, complexity, budget_percent, context_size
    condition_operator = Column(String(50), nullable=False)  # ==, !=, >, <, >=, <=, contains
    condition_value = Column(String(200), nullable=False)
    
    action_type = Column(String(50), nullable=False)  # ROUTE_TO, PREFER, FORCE_TIER, SET_POLICY
    action_target = Column(String(100), nullable=False)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class RequestRecord(Base):
    __tablename__ = "requests"

    request_id = Column(String(100), primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    prompt = Column(Text, nullable=False)
    task_type = Column(String(50), nullable=False)
    complexity = Column(Float, default=0.5)
    context_size = Column(Integer, default=0)
    reasoning_required = Column(Boolean, default=False)
    coding_required = Column(Boolean, default=False)
    
    routing_policy = Column(String(50), default="balanced")
    selected_model = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)
    status = Column(String(50), default="SUCCESS")  # SUCCESS, FAILED, FALLBACK
    
    fallback_used = Column(Boolean, default=False)
    original_model = Column(String(100), nullable=True)
    fallback_reason = Column(String(500), nullable=True)
    
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    baseline_cost = Column(Float, default=0.0)
    cost_saved = Column(Float, default=0.0)
    
    routing_latency_ms = Column(Float, default=0.0)
    provider_latency_ms = Column(Float, default=0.0)
    total_latency_ms = Column(Float, default=0.0)
    time_to_first_token_ms = Column(Float, nullable=True)


class RoutingDecisionRecord(Base):
    __tablename__ = "routing_decisions"

    decision_id = Column(String(100), primary_key=True)
    request_id = Column(String(100), ForeignKey("requests.request_id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    selected_model = Column(String(100), nullable=False)
    confidence = Column(Float, default=0.9)
    reasons = Column(JSON, default=list)
    candidate_scores = Column(JSON, default=dict)
    rejected_candidates = Column(JSON, default=dict)
    policy_used = Column(String(50), default="balanced")


class ResponseRecord(Base):
    __tablename__ = "responses"

    response_id = Column(String(100), primary_key=True)
    request_id = Column(String(100), ForeignKey("requests.request_id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    model_id = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    finish_reason = Column(String(50), default="stop")
    is_mock = Column(Boolean, default=False)


class FeedbackRecord(Base):
    __tablename__ = "feedback"

    id = Column(String(100), primary_key=True)
    request_id = Column(String(100), ForeignKey("requests.request_id"), nullable=False)
    model_id = Column(String(100), nullable=False)
    task_type = Column(String(50), nullable=False)
    rating = Column(Integer, nullable=False)  # 1 for thumbs up, -1 for thumbs down
    comment = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class BudgetRecord(Base):
    __tablename__ = "budgets"

    id = Column(String(50), primary_key=True, default="default")
    daily_limit = Column(Float, default=10.0)
    monthly_limit = Column(Float, default=100.0)
    per_request_limit = Column(Float, default=1.0)
    current_daily_spend = Column(Float, default=0.0)
    current_monthly_spend = Column(Float, default=0.0)
    intervention_mode = Column(String(50), default="OPTIMIZE")  # NORMAL, OPTIMIZE_80, CHEAP_95, BLOCK_100
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class ExperimentRecord(Base):
    __tablename__ = "experiments"

    id = Column(String(100), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    policy_a = Column(String(50), nullable=False)
    policy_b = Column(String(50), nullable=False)
    status = Column(String(50), default="ACTIVE")  # ACTIVE, PAUSED, COMPLETED
    sample_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ExperimentRunRecord(Base):
    __tablename__ = "experiment_runs"

    id = Column(String(100), primary_key=True)
    experiment_id = Column(String(100), ForeignKey("experiments.id"), nullable=False)
    request_id = Column(String(100), ForeignKey("requests.request_id"), nullable=False)
    assigned_policy = Column(String(50), nullable=False)
    selected_model = Column(String(100), nullable=False)
    cost = Column(Float, default=0.0)
    latency_ms = Column(Float, default=0.0)
    feedback_rating = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
