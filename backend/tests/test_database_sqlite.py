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
            results.append([journal, timeout])
        await engine.dispose()
    print(json.dumps(results))

asyncio.run(main())
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        env={**os.environ, "DATABASE_URL": url, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
        capture_output=True, text=True, check=True, timeout=30,
    )
    assert json.loads(result.stdout) == [["memory" if memory else "wal", 5000]] * 2


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
