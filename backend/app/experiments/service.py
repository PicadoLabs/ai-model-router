import uuid
import datetime
from typing import Dict, Any, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.storage.models import ExperimentRecord, ExperimentRunRecord


async def log_experiment_run(
    session: AsyncSession,
    experiment_id: str,
    request_id: str,
    policy: str,
    model: str,
    cost: float,
    latency_ms: float,
):
    run = ExperimentRunRecord(
        id=str(uuid.uuid4()),
        experiment_id=experiment_id,
        request_id=request_id,
        assigned_policy=policy,
        selected_model=model,
        cost=cost,
        latency_ms=latency_ms,
    )
    session.add(run)
    
    # Increment sample count
    res = await session.execute(select(ExperimentRecord).filter_by(id=experiment_id))
    exp = res.scalar_one_or_none()
    if exp:
        exp.sample_count += 1
    await session.commit()


async def get_experiment_summary(
    session: AsyncSession,
    experiment_id: str,
) -> Dict[str, Any]:
    res = await session.execute(select(ExperimentRecord).filter_by(id=experiment_id))
    exp = res.scalar_one_or_none()
    if not exp:
        return {}

    # Calculate metrics for Policy A vs Policy B
    runs_a = await session.execute(
        select(
            func.count(ExperimentRunRecord.id),
            func.avg(ExperimentRunRecord.cost),
            func.avg(ExperimentRunRecord.latency_ms),
        ).filter_by(experiment_id=experiment_id, assigned_policy=exp.policy_a)
    )
    count_a, cost_a, lat_a = runs_a.one()

    runs_b = await session.execute(
        select(
            func.count(ExperimentRunRecord.id),
            func.avg(ExperimentRunRecord.cost),
            func.avg(ExperimentRunRecord.latency_ms),
        ).filter_by(experiment_id=experiment_id, assigned_policy=exp.policy_b)
    )
    count_b, cost_b, lat_b = runs_b.one()

    return {
        "id": exp.id,
        "name": exp.name,
        "description": exp.description,
        "policy_a": exp.policy_a,
        "policy_b": exp.policy_b,
        "status": exp.status,
        "total_samples": exp.sample_count,
        "results": {
            exp.policy_a: {
                "sample_count": count_a or 0,
                "avg_cost_usd": round(cost_a or 0.0, 6),
                "avg_latency_ms": round(lat_a or 0.0, 1),
            },
            exp.policy_b: {
                "sample_count": count_b or 0,
                "avg_cost_usd": round(cost_b or 0.0, 6),
                "avg_latency_ms": round(lat_b or 0.0, 1),
            },
        },
    }
