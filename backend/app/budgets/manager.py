from typing import Tuple
from sqlalchemy import case, func, select, update
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
    if cost_to_add == 0.0:
        stmt = (
            select(BudgetRecord)
            .filter_by(id="default")
            .execution_options(autoflush=False)
        )
        res = await session.execute(stmt)
        budget = res.scalar_one_or_none()
        if not budget:
            return 0.0, "NORMAL"

        monthly_limit = budget.monthly_limit or 100.0
        percent = (
            (budget.current_monthly_spend / monthly_limit) * 100.0
            if monthly_limit > 0
            else 0.0
        )
        mode = "NORMAL"
        if percent >= 100.0:
            mode = "BLOCK_100"
        elif percent >= 95.0:
            mode = "CHEAP_95"
        elif percent >= 80.0:
            mode = "OPTIMIZE_80"

        return round(percent, 2), mode

    new_spend = BudgetRecord.current_monthly_spend + cost_to_add
    monthly_limit = func.coalesce(func.nullif(BudgetRecord.monthly_limit, 0.0), 100.0)
    percent = case(
        (monthly_limit > 0, new_spend / monthly_limit * 100.0),
        else_=0.0,
    )
    mode = case(
        (percent >= 100.0, "BLOCK_100"),
        (percent >= 95.0, "CHEAP_95"),
        (percent >= 80.0, "OPTIMIZE_80"),
        else_="NORMAL",
    )

    stmt = (
        update(BudgetRecord)
        .where(BudgetRecord.id == "default")
        .values(current_monthly_spend=new_spend, intervention_mode=mode)
        .returning(
            BudgetRecord.current_monthly_spend,
            BudgetRecord.monthly_limit,
            BudgetRecord.intervention_mode,
        )
    )
    result = await session.execute(stmt)
    updated_budget = result.one_or_none()
    if not updated_budget:
        return 0.0, "NORMAL"

    await session.commit()
    current_spend, monthly_limit, mode = updated_budget
    monthly_limit = monthly_limit or 100.0
    percent = (current_spend / monthly_limit) * 100.0 if monthly_limit > 0 else 0.0
    return round(percent, 2), mode
