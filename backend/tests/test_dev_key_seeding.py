"""Ensure init_db never seeds a predictable API credential outside local demos."""

import hashlib

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.storage import database
from app.storage.models import ApiKeyRecord


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("environment", "auth_required", "expect_dev_key"),
    [
        ("production", True, False),
        ("production", False, False),
        ("staging", False, False),
        ("development", True, False),
        ("development", False, True),
    ],
)
async def test_predictable_key_only_seeded_in_unprotected_development(
    monkeypatch, environment, auth_required, expect_dev_key
):
    # A fresh database per case ensures pre-existing keys cannot hide seeding.
    isolated_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    sessions = async_sessionmaker(isolated_engine, expire_on_commit=False)
    monkeypatch.setattr(database, "engine", isolated_engine)
    monkeypatch.setattr(database, "AsyncSessionLocal", sessions)
    monkeypatch.setattr(database.settings, "APP_ENV", environment)
    monkeypatch.setattr(database.settings, "AUTH_REQUIRED", auth_required)
    try:
        await database.init_db()
        async with sessions() as session:
            result = await session.execute(select(ApiKeyRecord))
            keys = result.scalars().all()
        assert len(keys) == int(expect_dev_key)
        if expect_dev_key:
            known_key_hash = hashlib.sha256(
                b"mr_live_dev_master_key_12345"
            ).hexdigest()
            assert keys[0].key_hash == known_key_hash
    finally:
        await isolated_engine.dispose()
