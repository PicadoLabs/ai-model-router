import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("memory", [False, True])
def test_sqlite_connections_configure_journal_and_timeout(tmp_path, memory):
    url = "sqlite+aiosqlite:///:memory:" if memory else f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    script = """
import asyncio
import json
from app.storage.database import engine

async def main():
    results = []
    for _ in range(2):
        async with engine.connect() as connection:
            journal = (await connection.exec_driver_sql('PRAGMA journal_mode')).scalar()
            timeout = (await connection.exec_driver_sql('PRAGMA busy_timeout')).scalar()
            foreign_keys = (await connection.exec_driver_sql('PRAGMA foreign_keys')).scalar()
            synchronous = (await connection.exec_driver_sql('PRAGMA synchronous')).scalar()
            results.append([journal, timeout, foreign_keys, synchronous])
        await engine.dispose()
    print(json.dumps(results))

asyncio.run(main())
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        env={**os.environ, "DATABASE_URL": url, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
        capture_output=True, text=True, check=True, timeout=30,
    )
    # synchronous=NORMAL reads back as 1
    assert json.loads(result.stdout) == [["memory" if memory else "wal", 5000, 1, 1]] * 2


@pytest.mark.asyncio
async def test_sqlite_foreign_keys_enforce_cascade(tmp_path):
    """The pragma is what makes ON DELETE CASCADE actually delete."""
    script = """
import asyncio
from app.storage.database import engine
from sqlalchemy import text

async def main():
    async with engine.begin() as connection:
        await connection.execute(text("CREATE TABLE parent (id INTEGER PRIMARY KEY)"))
        await connection.execute(text(
            "CREATE TABLE child (id INTEGER PRIMARY KEY, parent_id INTEGER "
            "REFERENCES parent(id) ON DELETE CASCADE)"
        ))
        await connection.execute(text("INSERT INTO parent (id) VALUES (1)"))
        await connection.execute(text("INSERT INTO child (id, parent_id) VALUES (10, 1)"))
        await connection.execute(text("DELETE FROM parent WHERE id = 1"))
        orphans = (await connection.execute(text("SELECT COUNT(*) FROM child"))).scalar()
    await engine.dispose()
    print(orphans)

asyncio.run(main())
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        env={**os.environ, "DATABASE_URL": f"sqlite+aiosqlite:///{tmp_path / 'fk.db'}", "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
        capture_output=True, text=True, check=True, timeout=30,
    )
    assert result.stdout.strip() == "0"


def test_sqlite_reader_does_not_block_concurrent_writers(tmp_path):
    script = """
import asyncio
from app.storage.database import engine

async def main():
    async with engine.begin() as connection:
        await connection.exec_driver_sql('CREATE TABLE writes (value INTEGER)')
        await connection.exec_driver_sql('INSERT INTO writes VALUES (0)')
    async with engine.connect() as reader:
        await reader.exec_driver_sql('BEGIN')
        assert (await reader.exec_driver_sql('SELECT COUNT(*) FROM writes')).scalar() == 1
        async def write(value):
            async with engine.begin() as writer:
                await writer.exec_driver_sql('INSERT INTO writes VALUES (?)', (value,))
        await asyncio.wait_for(asyncio.gather(*(write(i) for i in range(1, 17))), timeout=20)
        assert (await reader.exec_driver_sql('SELECT COUNT(*) FROM writes')).scalar() == 1
        await reader.rollback()
    async with engine.connect() as connection:
        assert (await connection.exec_driver_sql('SELECT COUNT(*) FROM writes')).scalar() == 17
    await engine.dispose()

asyncio.run(main())
"""
    subprocess.run(
        [sys.executable, "-c", script],
        env={**os.environ, "DATABASE_URL": f"sqlite+aiosqlite:///{tmp_path / 'concurrent.db'}", "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
        capture_output=True, text=True, check=True, timeout=30,
    )
