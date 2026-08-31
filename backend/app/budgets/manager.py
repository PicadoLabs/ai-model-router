from typing import Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.storage.models import BudgetRecord


async def check_budget_threshold(
    session: AsyncSession,
    cost_to_add: float = 0.0,
) -> Tuple[float, str]:
    """
    Checks current budget utilization percentage and determines intervention mode:
    - NORMAL (< 80%)
    - OPTIMIZE_80 (>= 80% and < 95%)
    - CHEAP_95 (>= 95% and < 100%)
    - BLOCK_100 (>= 100%)
    """
    res = await session.execute(select(BudgetRecord).filter_by(id="default"))
    budget = res.scalar_one_or_none()
    if not budget:
        return 0.0, "NORMAL"

    monthly_limit = budget.monthly_limit or 100.0
    current_spend = budget.current_monthly_spend + cost_to_add
    percent = (current_spend / monthly_limit) * 100.0 if monthly_limit > 0 else 0.0

    mode = "NORMAL"
    if percent >= 100.0:
        mode = "BLOCK_100"
    elif percent >= 95.0:
        mode = "CHEAP_95"
    elif percent >= 80.0:
        mode = "OPTIMIZE_80"

    budget.current_monthly_spend = current_spend
    budget.intervention_mode = mode
    await session.commit()

    return round(percent, 2), mode
