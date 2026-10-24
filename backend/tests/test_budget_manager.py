import asyncio

import pytest
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.budgets.manager import check_budget_threshold
from app.storage.database import AsyncSessionLocal, engine, init_db
from app.storage.models import BudgetRecord


@pytest.fixture
async def budget_record():
    await init_db()
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(BudgetRecord).filter_by(id="default"))
        budget = result.scalar_one()
        budget.monthly_limit = 100.0
        budget.current_monthly_spend = 92.0
        budget.intervention_mode = "NORMAL"
        await session.commit()


@pytest.mark.asyncio
async def test_concurrent_budget_updates_keep_spend_and_mode_consistent(budget_record):
    costs = [0.25] * 32

    async def add_cost(cost):
        async with AsyncSessionLocal() as session:
            return await check_budget_threshold(session, cost)

    results = await asyncio.wait_for(
        asyncio.gather(*(add_cost(cost) for cost in costs)),
        timeout=20,
    )

    assert len(results) == len(costs)
    assert max(percent for percent, _ in results) == 100.0
    assert (95.0, "CHEAP_95") in results
    assert (100.0, "BLOCK_100") in results
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(BudgetRecord).filter_by(id="default"))
        budget = result.scalar_one()

    assert budget.current_monthly_spend == 100.0
    assert budget.intervention_mode == "BLOCK_100"


@pytest.mark.asyncio
async def test_zero_cost_budget_check_is_read_only_and_returns_current_mode(
    budget_record, monkeypatch
):
    async def fail_commit(self):
        raise AssertionError("zero-cost budget checks must not commit")

    monkeypatch.setattr(AsyncSession, "commit", fail_commit)
    statements = []

    def capture_statement(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement.lstrip().split(None, 1)[0].upper())

    event.listen(engine.sync_engine, "before_cursor_execute", capture_statement)
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(BudgetRecord).filter_by(id="default"))
            budget = result.scalar_one()
            budget.current_monthly_spend = 96.0
            budget.intervention_mode = "CHEAP_95"
            result = await check_budget_threshold(session, 0.0)
            assert result == (96.0, "CHEAP_95")
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", capture_statement)

    assert not any(statement in {"INSERT", "UPDATE", "DELETE"} for statement in statements)

    async with AsyncSessionLocal() as session:
        persisted = await session.execute(
            select(BudgetRecord.current_monthly_spend, BudgetRecord.intervention_mode)
            .filter_by(id="default")
        )
        persisted_spend, persisted_mode = persisted.one()

    assert persisted_spend == 92.0
    assert persisted_mode == "NORMAL"


@pytest.mark.asyncio
async def test_failed_budget_commit_rolls_back_and_allows_retry(budget_record, monkeypatch):
    async def fail_commit(self):
        raise RuntimeError("Simulated budget commit failure")

    monkeypatch.setattr(AsyncSession, "commit", fail_commit)
    async with AsyncSessionLocal() as session:
        with pytest.raises(RuntimeError, match="Simulated budget commit failure"):
            await check_budget_threshold(session, 0.25)

    async with AsyncSessionLocal() as session:
        persisted = await session.execute(
            select(BudgetRecord.current_monthly_spend, BudgetRecord.intervention_mode)
            .filter_by(id="default")
        )
        assert persisted.one() == (92.0, "NORMAL")

    monkeypatch.undo()
    async with AsyncSessionLocal() as session:
        result = await check_budget_threshold(session, 0.25)
        assert result == (92.25, "OPTIMIZE_80")

    async with AsyncSessionLocal() as session:
        persisted = await session.execute(
            select(BudgetRecord.current_monthly_spend, BudgetRecord.intervention_mode)
            .filter_by(id="default")
        )
        assert persisted.one() == (92.25, "OPTIMIZE_80")
