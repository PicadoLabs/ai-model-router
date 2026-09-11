import uuid
import time
import asyncio
import csv
import io
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.storage.database import get_db
from app.storage.models import (
    ModelRecord,
    RoutingPolicyRecord,
    RoutingRuleRecord,
    RequestRecord,
    RoutingDecisionRecord,
    ResponseRecord,
    FeedbackRecord,
    BudgetRecord,
    ExperimentRecord,
)
from app.models.schemas import (
    ModelMetadata,
    RequestAnalysis,
    RoutingDecision,
    ProviderResponse,
    ModelTier,
)
from app.analyzer.analyzer import analyze_request
from app.router.engine import route_request
from app.fallback.handler import execute_with_fallback
from app.budgets.manager import check_budget_threshold
from app.observability.events import log_router_event
from app.analytics.service import get_system_analytics, calculate_cost_savings
from app.providers.registry import provider_registry
from app.config.settings import get_settings

router = APIRouter()
settings = get_settings()


class RouteOnlyRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Prompt text to analyze and route")
    policy: Optional[str] = None
    analyzer_mode: Optional[str] = None


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    system_prompt: Optional[str] = None
    policy: Optional[str] = None
    analyzer_mode: Optional[str] = None
    force_model: Optional[str] = None
    temperature: float = 0.7
    max_retries: int = 1


class FeedbackSubmitRequest(BaseModel):
    request_id: str
    rating: int = Field(..., description="1 for up, -1 for down")
    comment: Optional[str] = None


class ModelCreateRequest(BaseModel):
    id: str
    name: str
    provider: str
    type: str = "LOCAL"
    tier: str = "BALANCED"
    context_window: int = 32768
    supports_coding: bool = True
    supports_reasoning: bool = True
    supports_vision: bool = False
    supports_tools: bool = True
    quality_score: float = 0.85
    speed_score: float = 0.85
    cost_per_input_token: float = 0.0
    cost_per_output_token: float = 0.0


class RuleCreateRequest(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    priority: int = 10
    is_enabled: bool = True
    condition_field: str
    condition_operator: str
    condition_value: str
    action_type: str
    action_target: str


# Helper to convert DB model record to Pydantic ModelMetadata
def db_model_to_meta(m: ModelRecord) -> ModelMetadata:
    return ModelMetadata(
        id=m.id,
        name=m.name,
        provider=m.provider,
        type=m.type,
        tier=ModelTier(m.tier) if m.tier in [t.value for t in ModelTier] else ModelTier.BALANCED,
        context_window=m.context_window,
        supports_coding=m.supports_coding,
        supports_reasoning=m.supports_reasoning,
        supports_vision=m.supports_vision,
        supports_tools=m.supports_tools,
        quality_score=m.quality_score,
        speed_score=m.speed_score,
        reliability_score=m.reliability_score,
        cost_per_input_token=m.cost_per_input_token,
        cost_per_output_token=m.cost_per_output_token,
        availability=m.availability,
        is_active=m.is_active,
    )


@router.post("/api/route", response_model=Dict[str, Any])
async def api_route_prompt(req: RouteOnlyRequest, db: AsyncSession = Depends(get_db)):
    """
    Dry-run routing inspection endpoint:
    Analyzes request and produces structured routing decision without invoking provider.
    """
    t_start = time.perf_counter()
    req_id = f"req_{uuid.uuid4().hex[:12]}"
    
    # 1. Analyze Request
    analysis = await analyze_request(req.prompt, req.analyzer_mode)
    
    # 2. Fetch Models & Policy
    res_m = await db.execute(select(ModelRecord).filter_by(is_active=True))
    db_models = res_m.scalars().all()
    models = [db_model_to_meta(m) for m in db_models]

    policy_name = req.policy or settings.DEFAULT_ROUTING_POLICY
    res_p = await db.execute(select(RoutingPolicyRecord).filter_by(id=policy_name))
    policy = res_p.scalar_one_or_none()
    weights = {
        "quality_weight": policy.quality_weight if policy else 0.35,
        "cost_weight": policy.cost_weight if policy else 0.25,
        "speed_weight": policy.speed_weight if policy else 0.20,
        "capability_weight": policy.capability_weight if policy else 0.15,
        "reliability_weight": policy.reliability_weight if policy else 0.05,
    }

    # 3. Fetch Rules & Budget Check
    res_r = await db.execute(select(RoutingRuleRecord).filter_by(is_enabled=True))
    rules = res_r.scalars().all()
    budget_pct, _ = await check_budget_threshold(db, 0.0)

    # 4. Routing Decision
    decision = route_request(
        analysis=analysis,
        available_models=models,
        policy_weights=weights,
        policy_name=policy_name,
        rules=rules,
        budget_percent=budget_pct,
        request_id=req_id,
    )

    t_route_ms = (time.perf_counter() - t_start) * 1000.0

    return {
        "request_id": req_id,
        "analysis": analysis.model_dump(),
        "decision": decision.model_dump(),
        "routing_latency_ms": round(t_route_ms, 2),
    }


@router.post("/api/generate", response_model=Dict[str, Any])
async def api_generate_response(req: GenerateRequest, db: AsyncSession = Depends(get_db)):
    """
    End-to-End routed execution:
    Analyzes -> Routes -> Executes Selected Model / Fallback -> Records Decision & Metrics.
    """
    t_start = time.perf_counter()
    req_id = f"req_{uuid.uuid4().hex[:12]}"
    
    # 1. Analyze Request
    analysis = await analyze_request(req.prompt, req.analyzer_mode)

    # 2. Fetch Models & Policy
    res_m = await db.execute(select(ModelRecord).filter_by(is_active=True))
    db_models = res_m.scalars().all()
    models = [db_model_to_meta(m) for m in db_models]

    policy_name = req.policy or settings.DEFAULT_ROUTING_POLICY
    res_p = await db.execute(select(RoutingPolicyRecord).filter_by(id=policy_name))
    policy = res_p.scalar_one_or_none()
    weights = {
        "quality_weight": policy.quality_weight if policy else 0.35,
        "cost_weight": policy.cost_weight if policy else 0.25,
        "speed_weight": policy.speed_weight if policy else 0.20,
        "capability_weight": policy.capability_weight if policy else 0.15,
        "reliability_weight": policy.reliability_weight if policy else 0.05,
    }

    # 3. Fetch Rules & Budget Check
    res_r = await db.execute(select(RoutingRuleRecord).filter_by(is_enabled=True))
    rules = res_r.scalars().all()
    budget_pct, budget_mode = await check_budget_threshold(db, 0.0)

    # 4. Route
    decision = route_request(
        analysis=analysis,
        available_models=models,
        policy_weights=weights,
        policy_name=policy_name,
        rules=rules,
        budget_percent=budget_pct,
        request_id=req_id,
    )

    t_routing_done = time.perf_counter()
    routing_latency_ms = (t_routing_done - t_start) * 1000.0

    # If force model requested, override
    selected_model_id = req.force_model or decision.selected_model
    target_meta = next((m for m in models if m.id == selected_model_id), None)
    selected_provider_id = target_meta.provider if target_meta else decision.provider

    # 5. Provider Execution with Fallback & Retries
    provider_resp, fallback_used, orig_model, fallback_reason = await execute_with_fallback(
        prompt=req.prompt,
        selected_model_id=selected_model_id,
        selected_provider_id=selected_provider_id,
        all_models=models,
        system_prompt=req.system_prompt,
        temperature=req.temperature,
        max_retries=req.max_retries,
    )

    total_latency_ms = (time.perf_counter() - t_start) * 1000.0

    # 6. Calculate actual costs
    actual_model_meta = next((m for m in models if m.id == provider_resp.model), target_meta)
    cost_in_rate = actual_model_meta.cost_per_input_token if actual_model_meta else 0.0
    cost_out_rate = actual_model_meta.cost_per_output_token if actual_model_meta else 0.0
    actual_cost = round((provider_resp.input_tokens * cost_in_rate) + (provider_resp.output_tokens * cost_out_rate), 6)

    # Baseline cost calculation
    res_base = await db.execute(select(ModelRecord).filter_by(id=settings.BASELINE_MODEL_ID))
    base_m = res_base.scalar_one_or_none()
    base_cost = 0.0
    if base_m:
        base_cost = round((provider_resp.input_tokens * base_m.cost_per_input_token) + (provider_resp.output_tokens * base_m.cost_per_output_token), 6)
    saved_cost = max(0.0, round(base_cost - actual_cost, 6))

    # Update budget spend
    await check_budget_threshold(db, actual_cost)

    # 7. Persistence
    req_record = RequestRecord(
        request_id=req_id,
        prompt=req.prompt,
        task_type=analysis.task_type.value,
        complexity=analysis.complexity,
        context_size=analysis.context_size,
        reasoning_required=analysis.reasoning_required,
        coding_required=analysis.coding_required,
        routing_policy=policy_name,
        selected_model=provider_resp.model or selected_model_id,
        provider=provider_resp.provider or selected_provider_id,
        status="FALLBACK" if fallback_used else ("FAILED" if provider_resp.error else "SUCCESS"),
        fallback_used=fallback_used,
        original_model=orig_model,
        fallback_reason=fallback_reason,
        input_tokens=provider_resp.input_tokens,
        output_tokens=provider_resp.output_tokens,
        total_tokens=provider_resp.total_tokens,
        estimated_cost=actual_cost,
        baseline_cost=base_cost,
        cost_saved=saved_cost,
        routing_latency_ms=round(routing_latency_ms, 2),
        provider_latency_ms=round(provider_resp.provider_latency_ms, 2),
        total_latency_ms=round(total_latency_ms, 2),
        time_to_first_token_ms=provider_resp.time_to_first_token_ms,
    )
    db.add(req_record)

    decision_record = RoutingDecisionRecord(
        decision_id=decision.decision_id,
        request_id=req_id,
        selected_model=decision.selected_model,
        confidence=decision.confidence,
        reasons=decision.reasons,
        candidate_scores=[s.model_dump() for s in decision.candidate_scores],
        rejected_candidates=decision.rejected_candidates,
        policy_used=policy_name,
    )
    db.add(decision_record)

    resp_record = ResponseRecord(
        response_id=f"resp_{uuid.uuid4().hex[:12]}",
        request_id=req_id,
        model_id=provider_resp.model or selected_model_id,
        provider=provider_resp.provider or selected_provider_id,
        content=provider_resp.content,
        finish_reason=provider_resp.finish_reason,
        is_mock=provider_resp.is_mock,
    )
    db.add(resp_record)
    await db.commit()

    # 8. Structured Observability Event
    log_router_event(
        event_name="request_completed",
        request_id=req_id,
        model=provider_resp.model,
        provider=provider_resp.provider,
        duration_ms=round(total_latency_ms, 2),
        metadata={"tokens": provider_resp.total_tokens, "cost": actual_cost, "fallback": fallback_used},
    )

    return {
        "request_id": req_id,
        "analysis": analysis.model_dump(),
        "decision": decision.model_dump(),
        "response": provider_resp.model_dump(),
        "metrics": {
            "routing_latency_ms": round(routing_latency_ms, 2),
            "provider_latency_ms": round(provider_resp.provider_latency_ms, 2),
            "total_latency_ms": round(total_latency_ms, 2),
            "estimated_cost_usd": actual_cost,
            "baseline_cost_usd": base_cost,
            "cost_saved_usd": saved_cost,
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason,
        },
    }


# Models & Registry Endpoints
@router.get("/api/models")
async def list_models(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(ModelRecord).order_by(ModelRecord.tier, ModelRecord.name))
    return res.scalars().all()


@router.post("/api/models")
async def create_model(req: ModelCreateRequest, db: AsyncSession = Depends(get_db)):
    record = ModelRecord(
        id=req.id,
        name=req.name,
        provider=req.provider,
        type=req.type,
        tier=req.tier,
        context_window=req.context_window,
        supports_coding=req.supports_coding,
        supports_reasoning=req.supports_reasoning,
        supports_vision=req.supports_vision,
        supports_tools=req.supports_tools,
        quality_score=req.quality_score,
        speed_score=req.speed_score,
        cost_per_input_token=req.cost_per_input_token,
        cost_per_output_token=req.cost_per_output_token,
    )
    db.add(record)
    await db.commit()
    return record


# Providers Endpoint (Never returning secrets)
@router.get("/api/providers")
async def list_providers(db: AsyncSession = Depends(get_db)):
    providers_info = []
    for pid, p in provider_registry.list_providers().items():
        health = await p.check_health()
        providers_info.append({
            "id": pid,
            "name": p.name,
            "status": health.get("status", "READY"),
            "base_url": p.base_url,
            "message": health.get("message"),
            "models_available": health.get("models_available", []),
            "credentials_status": "Loaded from environment (.env)" if getattr(p, "api_key", None) or pid in ["mock", "ollama"] else "Not configured",
        })
    return providers_info


# Live Traffic & Decisions
@router.get("/api/traffic")
async def get_traffic_feed(limit: int = 50, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(RequestRecord).order_by(desc(RequestRecord.timestamp)).limit(limit))
    return res.scalars().all()


@router.get("/api/traffic/export")
async def export_traffic(
    format: str = Query("json", pattern="^(csv|json)$"),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(RequestRecord).order_by(desc(RequestRecord.timestamp)))
    records = res.scalars().all()
    fields = [
        "timestamp",
        "request_id",
        "prompt_preview",
        "task_type",
        "complexity",
        "selected_model",
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "cost_saved",
        "total_latency_ms",
    ]
    rows = [
        {
            "timestamp": record.timestamp.isoformat() if record.timestamp else "",
            "request_id": record.request_id,
            "prompt_preview": record.prompt[:200],
            "task_type": record.task_type,
            "complexity": record.complexity,
            "selected_model": record.selected_model,
            "input_tokens": record.input_tokens,
            "output_tokens": record.output_tokens,
            "total_tokens": record.total_tokens,
            "cost_saved": record.cost_saved,
            "total_latency_ms": record.total_latency_ms,
        }
        for record in records
    ]

    if format == "json":
        return JSONResponse(
            content=rows,
            headers={"Content-Disposition": "attachment; filename=traffic-export.json"},
        )

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=traffic-export.csv"},
    )


@router.get("/api/decisions/{decision_id_or_request_id}")
async def get_decision_details(decision_id_or_request_id: str, db: AsyncSession = Depends(get_db)):
    res_dec = await db.execute(
        select(RoutingDecisionRecord).filter(
            (RoutingDecisionRecord.decision_id == decision_id_or_request_id)
            | (RoutingDecisionRecord.request_id == decision_id_or_request_id)
        )
    )
    dec = res_dec.scalar_one_or_none()
    if not dec:
        raise HTTPException(status_code=404, detail="Decision not found")

    res_req = await db.execute(select(RequestRecord).filter_by(request_id=dec.request_id))
    req = res_req.scalar_one_or_none()

    res_resp = await db.execute(select(ResponseRecord).filter_by(request_id=dec.request_id))
    resp = res_resp.scalar_one_or_none()

    return {
        "decision": dec,
        "request": req,
        "response": resp,
    }


# Feedback
@router.post("/api/feedback")
async def submit_feedback(req: FeedbackSubmitRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(RequestRecord).filter_by(request_id=req.request_id))
    request_rec = res.scalar_one_or_none()
    if not request_rec:
        raise HTTPException(status_code=404, detail="Request ID not found")

    feedback = FeedbackRecord(
        id=f"fb_{uuid.uuid4().hex[:10]}",
        request_id=req.request_id,
        model_id=request_rec.selected_model,
        task_type=request_rec.task_type,
        rating=1 if req.rating > 0 else -1,
        comment=req.comment,
    )
    db.add(feedback)
    await db.commit()
    return {"status": "success", "feedback_id": feedback.id}


# Analytics Endpoints
@router.get("/api/analytics")
async def get_analytics(db: AsyncSession = Depends(get_db)):
    return await get_system_analytics(db)


@router.get("/api/analytics/savings")
async def get_savings(baseline_model: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    return await calculate_cost_savings(db, baseline_model)


# Rules Endpoints
@router.get("/api/rules")
async def list_rules(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(RoutingRuleRecord).order_by(desc(RoutingRuleRecord.priority)))
    return res.scalars().all()


@router.post("/api/rules")
async def create_rule(req: RuleCreateRequest, db: AsyncSession = Depends(get_db)):
    rule_id = req.id or f"rule-{uuid.uuid4().hex[:8]}"
    record = RoutingRuleRecord(
        id=rule_id,
        name=req.name,
        description=req.description,
        priority=req.priority,
        is_enabled=req.is_enabled,
        condition_field=req.condition_field,
        condition_operator=req.condition_operator,
        condition_value=req.condition_value,
        action_type=req.action_type,
        action_target=req.action_target,
    )
    db.add(record)
    await db.commit()
    return record


@router.put("/api/rules/{rule_id}")
async def update_rule(rule_id: str, req: RuleCreateRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(RoutingRuleRecord).filter_by(id=rule_id))
    rule = res.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.name = req.name
    rule.description = req.description
    rule.priority = req.priority
    rule.is_enabled = req.is_enabled
    rule.condition_field = req.condition_field
    rule.condition_operator = req.condition_operator
    rule.condition_value = req.condition_value
    rule.action_type = req.action_type
    rule.action_target = req.action_target
    await db.commit()
    return rule


@router.delete("/api/rules/{rule_id}")
async def delete_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(RoutingRuleRecord).filter_by(id=rule_id))
    rule = res.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await db.delete(rule)
    await db.commit()
    return {"status": "deleted", "id": rule_id}


# Policies
@router.get("/api/policies")
async def list_policies(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(RoutingPolicyRecord))
    return res.scalars().all()


# Budgets
@router.get("/api/budgets")
async def get_budget(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(BudgetRecord).filter_by(id="default"))
    return res.scalar_one_or_none()


# Experiments
@router.get("/api/experiments")
async def list_experiments(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(ExperimentRecord))
    return res.scalars().all()


# Health Check
@router.get("/api/health")
async def get_health():
    return {
        "status": "healthy",
        "service": "Model Router AI Control Room",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
    }
