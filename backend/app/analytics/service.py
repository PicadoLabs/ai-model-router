from typing import Dict, Any, List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.storage.models import RequestRecord, FeedbackRecord, ModelRecord
from app.config.settings import get_settings

settings = get_settings()


async def calculate_cost_savings(
    session: AsyncSession,
    baseline_model_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Computes accurate, non-invented cost savings:
    Baseline Cost (if all requests were sent to baseline model) vs Actual Routed Cost.
    """
    base_id = baseline_model_id or settings.BASELINE_MODEL_ID
    
    # Fetch baseline model pricing
    res_base = await session.execute(select(ModelRecord).filter_by(id=base_id))
    baseline_model = res_base.scalar_one_or_none()
    
    base_in_rate = baseline_model.cost_per_input_token if baseline_model else 0.000005
    base_out_rate = baseline_model.cost_per_output_token if baseline_model else 0.000015

    # Fetch aggregate requests
    res = await session.execute(
        select(
            func.count(RequestRecord.request_id),
            func.sum(RequestRecord.input_tokens),
            func.sum(RequestRecord.output_tokens),
            func.sum(RequestRecord.estimated_cost),
        )
    )
    total_reqs, total_in_tok, total_out_tok, total_routed_cost = res.one()

    total_reqs = total_reqs or 0
    total_in_tok = total_in_tok or 0
    total_out_tok = total_out_tok or 0
    total_routed_cost = round(total_routed_cost or 0.0, 6)

    # Theoretical cost if all traffic ran on baseline
    baseline_total_cost = round((total_in_tok * base_in_rate) + (total_out_tok * base_out_rate), 6)
    saved_amount = max(0.0, round(baseline_total_cost - total_routed_cost, 6))
    savings_percent = round((saved_amount / baseline_total_cost * 100.0), 2) if baseline_total_cost > 0 else 0.0

    return {
        "baseline_model": base_id,
        "total_requests": total_reqs,
        "total_input_tokens": total_in_tok,
        "total_output_tokens": total_out_tok,
        "baseline_total_cost": baseline_total_cost,
        "routed_total_cost": total_routed_cost,
        "cost_saved_usd": saved_amount,
        "savings_percentage": savings_percent,
    }


async def get_system_analytics(session: AsyncSession) -> Dict[str, Any]:
    """
    Collects full aggregate metrics for the dashboard.
    """
    # 1. Totals & averages
    res = await session.execute(
        select(
            func.count(RequestRecord.request_id),
            func.avg(RequestRecord.total_latency_ms),
            func.avg(RequestRecord.routing_latency_ms),
            func.avg(RequestRecord.estimated_cost),
            func.sum(RequestRecord.estimated_cost),
        )
    )
    count, avg_lat, avg_route_lat, avg_cost, sum_cost = res.one()

    # 2. Distribution by model
    model_dist_res = await session.execute(
        select(RequestRecord.selected_model, func.count(RequestRecord.request_id))
        .group_by(RequestRecord.selected_model)
    )
    model_distribution = {m: c for m, c in model_dist_res.all()}

    # 3. Distribution by task type
    task_dist_res = await session.execute(
        select(RequestRecord.task_type, func.count(RequestRecord.request_id))
        .group_by(RequestRecord.task_type)
    )
    task_distribution = {t: c for t, c in task_dist_res.all()}

    # 4. Fallback rate
    fb_res = await session.execute(
        select(func.count(RequestRecord.request_id)).filter(RequestRecord.fallback_used == True)
    )
    fallback_count = fb_res.scalar() or 0
    fallback_rate = round((fallback_count / count * 100.0), 2) if count and count > 0 else 0.0

    # 5. User Feedback aggregate
    fb_pos_res = await session.execute(select(func.count(FeedbackRecord.id)).filter(FeedbackRecord.rating == 1))
    fb_neg_res = await session.execute(select(func.count(FeedbackRecord.id)).filter(FeedbackRecord.rating == -1))
    pos_feedback = fb_pos_res.scalar() or 0
    neg_feedback = fb_neg_res.scalar() or 0
    total_feedback = pos_feedback + neg_feedback
    quality_score = round((pos_feedback / total_feedback * 100.0), 1) if total_feedback > 0 else None

    savings = await calculate_cost_savings(session)

    return {
        "total_requests": count or 0,
        "avg_latency_ms": round(avg_lat or 0.0, 1),
        "avg_routing_latency_ms": round(avg_route_lat or 0.0, 1),
        "avg_cost_usd": round(avg_cost or 0.0, 6),
        "total_cost_usd": round(sum_cost or 0.0, 6),
        "quality_score_percent": quality_score,
        "fallback_rate_percent": fallback_rate,
        "fallback_count": fallback_count,
        "model_distribution": model_distribution,
        "task_distribution": task_distribution,
        "savings": savings,
    }
