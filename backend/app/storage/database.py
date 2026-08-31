from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config.settings import get_settings
from app.storage.models import (
    Base,
    ModelRecord,
    ProviderRecord,
    RoutingPolicyRecord,
    RoutingRuleRecord,
    BudgetRecord,
)

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Populate initial seed data if empty
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        
        # Check providers
        res = await session.execute(select(ProviderRecord))
        providers = res.scalars().all()
        if not providers:
            default_providers = [
                ProviderRecord(id="mock", name="Mock / Demo Provider", status="CONNECTED", is_enabled=True),
                ProviderRecord(id="ollama", name="Ollama (Local)", status="READY", is_enabled=True, base_url=settings.OLLAMA_BASE_URL),
                ProviderRecord(id="openai", name="OpenAI", status="CONNECTED" if settings.OPENAI_API_KEY else "NOT_CONFIGURED", is_enabled=bool(settings.OPENAI_API_KEY)),
                ProviderRecord(id="anthropic", name="Anthropic", status="CONNECTED" if settings.ANTHROPIC_API_KEY else "NOT_CONFIGURED", is_enabled=bool(settings.ANTHROPIC_API_KEY)),
                ProviderRecord(id="gemini", name="Google Gemini", status="CONNECTED" if settings.GEMINI_API_KEY else "NOT_CONFIGURED", is_enabled=bool(settings.GEMINI_API_KEY)),
            ]
            session.add_all(default_providers)
        
        # Check models
        res_m = await session.execute(select(ModelRecord))
        models = res_m.scalars().all()
        if not models:
            default_models = [
                # Mock Models
                ModelRecord(
                    id="mock-fast",
                    name="Mock Fast (Echo)",
                    provider="mock",
                    type="MOCK",
                    tier="FAST",
                    context_window=32768,
                    supports_coding=True,
                    supports_reasoning=False,
                    supports_vision=False,
                    supports_tools=True,
                    quality_score=0.75,
                    speed_score=0.98,
                    reliability_score=0.99,
                    cost_per_input_token=0.0000001,
                    cost_per_output_token=0.0000002,
                ),
                ModelRecord(
                    id="mock-balanced",
                    name="Mock Balanced (General)",
                    provider="mock",
                    type="MOCK",
                    tier="BALANCED",
                    context_window=65536,
                    supports_coding=True,
                    supports_reasoning=True,
                    supports_vision=True,
                    supports_tools=True,
                    quality_score=0.88,
                    speed_score=0.85,
                    reliability_score=0.99,
                    cost_per_input_token=0.000001,
                    cost_per_output_token=0.000003,
                ),
                ModelRecord(
                    id="mock-power",
                    name="Mock Power (Reasoning)",
                    provider="mock",
                    type="MOCK",
                    tier="POWER",
                    context_window=131072,
                    supports_coding=True,
                    supports_reasoning=True,
                    supports_vision=True,
                    supports_tools=True,
                    quality_score=0.98,
                    speed_score=0.60,
                    reliability_score=0.99,
                    cost_per_input_token=0.000005,
                    cost_per_output_token=0.000015,
                ),
                # Local Ollama Models (Default profiles)
                ModelRecord(
                    id="ollama-qwen2.5-coder",
                    name="Qwen 2.5 Coder 7B (Ollama)",
                    provider="ollama",
                    type="LOCAL",
                    tier="FAST",
                    context_window=32768,
                    supports_coding=True,
                    supports_reasoning=True,
                    supports_vision=False,
                    supports_tools=True,
                    quality_score=0.86,
                    speed_score=0.92,
                    reliability_score=0.95,
                    cost_per_input_token=0.0,
                    cost_per_output_token=0.0,
                ),
                ModelRecord(
                    id="ollama-llama3.2",
                    name="Llama 3.2 3B (Ollama)",
                    provider="ollama",
                    type="LOCAL",
                    tier="FAST",
                    context_window=131072,
                    supports_coding=True,
                    supports_reasoning=True,
                    supports_vision=False,
                    supports_tools=True,
                    quality_score=0.82,
                    speed_score=0.95,
                    reliability_score=0.95,
                    cost_per_input_token=0.0,
                    cost_per_output_token=0.0,
                ),
                ModelRecord(
                    id="ollama-mistral",
                    name="Mistral 7B (Ollama)",
                    provider="ollama",
                    type="LOCAL",
                    tier="BALANCED",
                    context_window=32768,
                    supports_coding=True,
                    supports_reasoning=True,
                    supports_vision=False,
                    supports_tools=True,
                    quality_score=0.84,
                    speed_score=0.88,
                    reliability_score=0.95,
                    cost_per_input_token=0.0,
                    cost_per_output_token=0.0,
                ),
                ModelRecord(
                    id="ollama-deepseek-r1",
                    name="DeepSeek R1 8B (Ollama)",
                    provider="ollama",
                    type="LOCAL",
                    tier="POWER",
                    context_window=65536,
                    supports_coding=True,
                    supports_reasoning=True,
                    supports_vision=False,
                    supports_tools=False,
                    quality_score=0.93,
                    speed_score=0.68,
                    reliability_score=0.94,
                    cost_per_input_token=0.0,
                    cost_per_output_token=0.0,
                ),
                # External Cloud Model Profiles
                ModelRecord(
                    id="gpt-4o-mini",
                    name="OpenAI GPT-4o Mini",
                    provider="openai",
                    type="CLOUD",
                    tier="FAST",
                    context_window=128000,
                    supports_coding=True,
                    supports_reasoning=True,
                    supports_vision=True,
                    supports_tools=True,
                    quality_score=0.88,
                    speed_score=0.90,
                    reliability_score=0.99,
                    cost_per_input_token=0.00000015,
                    cost_per_output_token=0.00000060,
                ),
                ModelRecord(
                    id="gpt-4o",
                    name="OpenAI GPT-4o",
                    provider="openai",
                    type="CLOUD",
                    tier="POWER",
                    context_window=128000,
                    supports_coding=True,
                    supports_reasoning=True,
                    supports_vision=True,
                    supports_tools=True,
                    quality_score=0.96,
                    speed_score=0.75,
                    reliability_score=0.99,
                    cost_per_input_token=0.0000025,
                    cost_per_output_token=0.000010,
                ),
                ModelRecord(
                    id="claude-3-5-sonnet",
                    name="Anthropic Claude 3.5 Sonnet",
                    provider="anthropic",
                    type="CLOUD",
                    tier="POWER",
                    context_window=200000,
                    supports_coding=True,
                    supports_reasoning=True,
                    supports_vision=True,
                    supports_tools=True,
                    quality_score=0.98,
                    speed_score=0.72,
                    reliability_score=0.99,
                    cost_per_input_token=0.000003,
                    cost_per_output_token=0.000015,
                ),
                ModelRecord(
                    id="gemini-1.5-flash",
                    name="Google Gemini 1.5 Flash",
                    provider="gemini",
                    type="CLOUD",
                    tier="FAST",
                    context_window=1000000,
                    supports_coding=True,
                    supports_reasoning=True,
                    supports_vision=True,
                    supports_tools=True,
                    quality_score=0.87,
                    speed_score=0.93,
                    reliability_score=0.99,
                    cost_per_input_token=0.000000075,
                    cost_per_output_token=0.00000030,
                ),
            ]
            session.add_all(default_models)

        # Check policies
        res_p = await session.execute(select(RoutingPolicyRecord))
        policies = res_p.scalars().all()
        if not policies:
            default_policies = [
                RoutingPolicyRecord(
                    id="balanced",
                    name="Balanced Router",
                    description="Optimizes across quality, cost, speed, capabilities, and reliability.",
                    quality_weight=0.35,
                    cost_weight=0.25,
                    speed_weight=0.20,
                    capability_weight=0.15,
                    reliability_weight=0.05,
                    is_default=True,
                ),
                RoutingPolicyRecord(
                    id="lowest_cost",
                    name="Lowest Cost",
                    description="Prefers cheapest and local zero-cost models with acceptable capability.",
                    quality_weight=0.15,
                    cost_weight=0.60,
                    speed_weight=0.15,
                    capability_weight=0.05,
                    reliability_weight=0.05,
                    is_default=False,
                ),
                RoutingPolicyRecord(
                    id="lowest_latency",
                    name="Lowest Latency",
                    description="Prefers fastest response times and high throughput models.",
                    quality_weight=0.15,
                    cost_weight=0.15,
                    speed_weight=0.60,
                    capability_weight=0.05,
                    reliability_weight=0.05,
                    is_default=False,
                ),
                RoutingPolicyRecord(
                    id="highest_quality",
                    name="Highest Quality",
                    description="Directs all complex reasoning and coding tasks to top-tier frontier models.",
                    quality_weight=0.65,
                    cost_weight=0.05,
                    speed_weight=0.10,
                    capability_weight=0.15,
                    reliability_weight=0.05,
                    is_default=False,
                ),
                RoutingPolicyRecord(
                    id="custom",
                    name="Custom Weights",
                    description="User-defined policy weights.",
                    quality_weight=0.30,
                    cost_weight=0.30,
                    speed_weight=0.20,
                    capability_weight=0.10,
                    reliability_weight=0.10,
                    is_default=False,
                ),
            ]
            session.add_all(default_policies)

        # Check default budget
        res_b = await session.execute(select(BudgetRecord))
        budget = res_b.scalar_one_or_none()
        if not budget:
            session.add(
                BudgetRecord(
                    id="default",
                    daily_limit=settings.DAILY_BUDGET,
                    monthly_limit=settings.MONTHLY_BUDGET,
                    per_request_limit=settings.PER_REQUEST_BUDGET,
                    current_daily_spend=0.0,
                    current_monthly_spend=0.0,
                    intervention_mode="NORMAL",
                )
            )

        # Check default rules
        res_r = await session.execute(select(RoutingRuleRecord))
        rules = res_r.scalars().all()
        if not rules:
            default_rules = [
                RoutingRuleRecord(
                    id="rule-code-reasoning",
                    name="Deep Debugging & Reasoning Override",
                    description="Route high complexity coding & debugging to Power Models",
                    priority=10,
                    is_enabled=True,
                    condition_field="task_type",
                    condition_operator="==",
                    condition_value="DEBUGGING",
                    action_type="FORCE_TIER",
                    action_target="POWER",
                ),
                RoutingRuleRecord(
                    id="rule-budget-saver",
                    name="Budget Guard > 95%",
                    description="Prefer local or fast models when budget exceeds 95%",
                    priority=50,
                    is_enabled=True,
                    condition_field="budget_percent",
                    condition_operator=">=",
                    condition_value="95.0",
                    action_type="SET_POLICY",
                    action_target="lowest_cost",
                ),
            ]
            session.add_all(default_rules)

        await session.commit()
