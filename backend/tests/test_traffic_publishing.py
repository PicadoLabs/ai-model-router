"""
Focused tests for post-commit live traffic publishing to InMemoryTrafficBroadcaster.

Verifies:
1. Non-streaming request-completion path publishes traffic payload after successful DB commit.
2. Streaming request-completion path publishes traffic payload after successful DB commit.
3. The event payload schema preserves all 10 traffic fields and valid serialization.
4. Database commit failures do not result in published live traffic events.
5. Zero additional database queries are executed when publishing.
6. Non-blocking resilience: broadcaster errors do not bubble up or fail the request.
7. Multi-subscriber fan-out from real request handlers.
"""
import asyncio
import datetime
import json
from unittest.mock import patch, MagicMock
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from app.storage.database import init_db, engine
from app.storage.models import RequestRecord
from app.storage.events_channel import get_broadcaster
from app.api.routes import build_traffic_event_payload, _publish_in_memory_traffic_event


EXPECTED_TRAFFIC_FIELDS = {
    "request_id",
    "timestamp",
    "prompt",
    "task_type",
    "complexity",
    "selected_model",
    "provider",
    "status",
    "total_latency_ms",
    "estimated_cost",
}


@pytest.fixture(autouse=True)
async def setup_test_environment():
    """Ensure database is initialized and clear broadcaster subscribers between tests."""
    await init_db()
    broadcaster = get_broadcaster()
    broadcaster.clear()
    yield
    broadcaster.clear()


# =========================================================================
# 1. Payload Schema & Serialization Tests
# =========================================================================

def test_build_traffic_event_payload_schema_and_types():
    """Verify that build_traffic_event_payload produces all 10 expected fields with correct types."""
    fixed_time = datetime.datetime(2026, 10, 21, 14, 30, 0, tzinfo=datetime.timezone.utc)
    rec = RequestRecord(
        request_id="req_test_abc123",
        timestamp=fixed_time,
        prompt="Write a Python script to sort numbers",
        task_type="CODING",
        complexity=0.65,
        selected_model="mock-balanced",
        provider="mock",
        status="SUCCESS",
        total_latency_ms=145.2,
        estimated_cost=0.00045,
    )

    payload = build_traffic_event_payload(rec)

    assert set(payload.keys()) == EXPECTED_TRAFFIC_FIELDS
    assert payload["request_id"] == "req_test_abc123"
    assert payload["timestamp"] == fixed_time.isoformat()
    assert payload["prompt"] == "Write a Python script to sort numbers"
    assert payload["task_type"] == "CODING"
    assert payload["complexity"] == 0.65
    assert payload["selected_model"] == "mock-balanced"
    assert payload["provider"] == "mock"
    assert payload["status"] == "SUCCESS"
    assert payload["total_latency_ms"] == 145.2
    assert payload["estimated_cost"] == 0.00045

    # Verify JSON serialization round-trip
    dumped = json.dumps(payload)
    loaded = json.loads(dumped)
    assert loaded == payload


def test_build_traffic_event_payload_handles_missing_or_empty_timestamp():
    """Verify that build_traffic_event_payload provides a valid ISO timestamp if rec.timestamp is None."""
    rec = RequestRecord(
        request_id="req_test_no_ts",
        prompt="Test without timestamp",
        task_type="GENERAL_QA",
        complexity=0.3,
        selected_model="mock-fast",
        provider="mock",
        status="SUCCESS",
        total_latency_ms=80.0,
        estimated_cost=0.0001,
    )
    rec.timestamp = None

    payload = build_traffic_event_payload(rec)

    assert "timestamp" in payload
    assert isinstance(payload["timestamp"], str)
    assert len(payload["timestamp"]) > 0
    # Must be parseable as ISO datetime
    parsed_dt = datetime.datetime.fromisoformat(payload["timestamp"])
    assert parsed_dt is not None


# =========================================================================
# 2. Non-Streaming Request-Completion Publishing Tests
# =========================================================================

@pytest.mark.asyncio
async def test_non_streaming_generate_publishes_traffic_payload_after_commit():
    """Verify that POST /api/generate publishes exactly one payload to subscriber after DB commit."""
    broadcaster = get_broadcaster()
    queue = broadcaster.subscribe()
    assert queue.empty()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        req_payload = {
            "prompt": "Explain asyncio in Python",
            "policy": "balanced",
        }
        res = await client.post("/api/generate", json=req_payload)
        assert res.status_code == 200
        data = res.json()
        req_id = data["request_id"]

    assert queue.qsize() == 1
    event_payload = queue.get_nowait()

    assert set(event_payload.keys()) == EXPECTED_TRAFFIC_FIELDS
    assert event_payload["request_id"] == req_id
    assert event_payload["prompt"] == "Explain asyncio in Python"
    expected_status = "FALLBACK" if data["metrics"]["fallback_used"] else ("FAILED" if data["response"]["error"] else "SUCCESS")
    assert event_payload["status"] == expected_status
    assert event_payload["selected_model"] == (data["response"]["model"] or data["decision"]["selected_model"])
    assert event_payload["provider"] in ["mock", "ollama", "openai", "anthropic", "gemini"]
    assert isinstance(event_payload["total_latency_ms"], (int, float))
    assert isinstance(event_payload["estimated_cost"], (int, float))
    assert isinstance(event_payload["complexity"], (int, float))
    assert isinstance(event_payload["timestamp"], str)


@pytest.mark.asyncio
async def test_non_streaming_db_commit_failure_does_not_publish():
    """Verify that if database commit fails, no live traffic event is published."""
    broadcaster = get_broadcaster()
    queue = broadcaster.subscribe()
    assert queue.empty()

    transport = ASGITransport(app=app)
    # Monkeypatch AsyncSession.commit to simulate failure on commit
    with patch.object(AsyncSession, "commit", side_effect=RuntimeError("Simulated DB commit error")):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            req_payload = {
                "prompt": "Test commit failure behavior",
                "policy": "balanced",
            }
            with pytest.raises(RuntimeError, match="Simulated DB commit error"):
                await client.post("/api/generate", json=req_payload)

    # Event must NOT be published because commit failed
    assert queue.empty()
    assert queue.qsize() == 0


# =========================================================================
# 3. Streaming Request-Completion Publishing Tests
# =========================================================================

@pytest.mark.asyncio
async def test_streaming_generate_publishes_traffic_payload_after_commit():
    """Verify that streaming POST /api/generate publishes a payload to subscriber after DB commit."""
    broadcaster = get_broadcaster()
    queue = broadcaster.subscribe()
    assert queue.empty()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        req_payload = {
            "prompt": "Stream a short greeting",
            "policy": "balanced",
            "stream": True,
        }
        async with client.stream("POST", "/api/generate", json=req_payload) as resp:
            assert resp.status_code == 200
            chunks = []
            async for chunk in resp.aiter_text():
                chunks.append(chunk)

            stream_text = "".join(chunks)
            assert "event: done" in stream_text

    assert queue.qsize() == 1
    event_payload = queue.get_nowait()

    assert set(event_payload.keys()) == EXPECTED_TRAFFIC_FIELDS
    assert event_payload["prompt"] == "Stream a short greeting"
    assert event_payload["status"] == "SUCCESS"
    assert event_payload["selected_model"] != ""
    assert isinstance(event_payload["total_latency_ms"], (int, float))
    assert isinstance(event_payload["estimated_cost"], (int, float))
    assert isinstance(event_payload["timestamp"], str)


@pytest.mark.asyncio
async def test_streaming_db_commit_failure_does_not_publish():
    """Verify that if database commit fails in streaming path, no live traffic event is published."""
    broadcaster = get_broadcaster()
    queue = broadcaster.subscribe()
    assert queue.empty()

    transport = ASGITransport(app=app)
    with patch.object(AsyncSession, "commit", side_effect=RuntimeError("Stream DB commit error")):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            req_payload = {
                "prompt": "Stream commit failure test",
                "stream": True,
            }
            try:
                async with client.stream("POST", "/api/generate", json=req_payload) as resp:
                    async for _ in resp.aiter_text():
                        pass
            except Exception:
                pass

    # Event must NOT be published
    assert queue.empty()
    assert queue.qsize() == 0


# =========================================================================
# 4. Zero Additional Database Queries Verification
# =========================================================================

@pytest.mark.asyncio
async def test_publishing_requires_no_additional_database_queries():
    """
    Verify that constructing and publishing the traffic payload from in-memory RequestRecord
    executes zero additional SQL queries against the database engine.
    """
    rec = RequestRecord(
        request_id="req_query_test_1",
        timestamp=datetime.datetime.now(datetime.timezone.utc),
        prompt="Query test prompt",
        task_type="GENERAL_QA",
        complexity=0.5,
        selected_model="mock-balanced",
        provider="mock",
        status="SUCCESS",
        total_latency_ms=50.0,
        estimated_cost=0.0002,
    )

    query_count = 0

    def query_listener(conn, cursor, statement, parameters, context, executemany):
        nonlocal query_count
        query_count += 1

    # Attach event listener to SQLite sync engine to intercept any SQL execution
    event.listen(engine.sync_engine, "before_cursor_execute", query_listener)
    try:
        broadcaster = get_broadcaster()
        queue = broadcaster.subscribe()

        initial_count = query_count

        # Build payload and publish
        _publish_in_memory_traffic_event(rec)

        assert query_count == initial_count, f"Expected 0 queries, got {query_count - initial_count}"
        assert queue.qsize() == 1
        payload = queue.get_nowait()
        assert payload["request_id"] == "req_query_test_1"
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", query_listener)


# =========================================================================
# 5. Non-Blocking Resilience & Multi-Subscriber Fan-Out
# =========================================================================

def test_publish_helper_handles_broadcaster_exceptions_gracefully():
    """Verify that if broadcaster.publish_nowait raises, _publish_in_memory_traffic_event does not fail."""
    rec = RequestRecord(
        request_id="req_err_resilience",
        prompt="Error test",
        task_type="GENERAL_QA",
        complexity=0.5,
        selected_model="mock-fast",
        provider="mock",
        status="SUCCESS",
        total_latency_ms=10.0,
        estimated_cost=0.0001,
    )

    with patch.object(get_broadcaster(), "publish_nowait", side_effect=Exception("Unexpected queue failure")):
        # Should not raise exception
        _publish_in_memory_traffic_event(rec)


@pytest.mark.asyncio
async def test_fanout_to_multiple_subscribers():
    """Verify that multiple concurrent subscribers all receive the published event from /api/generate."""
    broadcaster = get_broadcaster()
    queue1 = broadcaster.subscribe()
    queue2 = broadcaster.subscribe()
    queue3 = broadcaster.subscribe()
    assert broadcaster.subscriber_count == 3

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/generate", json={"prompt": "Broadcast to 3 clients"})
        assert res.status_code == 200

    assert queue1.qsize() == 1
    assert queue2.qsize() == 1
    assert queue3.qsize() == 1

    item1 = queue1.get_nowait()
    item2 = queue2.get_nowait()
    item3 = queue3.get_nowait()

    assert item1 == item2 == item3
    assert item1["prompt"] == "Broadcast to 3 clients"
