"""
Integration tests for the live traffic SSE endpoint (/api/traffic/stream).

Verifies:
1. Effective route works without Redis (in-memory fallback), returning 200 text/event-stream.
2. Initial database snapshot is sent when a RequestRecord exists.
3. No repeated database queries while waiting for or receiving live events.
4. Newly published in-memory events reach connected SSE clients.
5. Multiple concurrent connected clients all receive broadcast events.
6. Disconnecting one client cleans up its subscriber queue without affecting other clients.
7. Deduplication between initial snapshot and queued events prevents double emission.
8. Redis Pub/Sub path yields normalized traffic_event payloads matching the frontend contract.
9. Empty database on client connect does not yield corrupt snapshots and waits cleanly.
"""
import asyncio
import datetime
import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from sqlalchemy import event, desc, select, delete

from app.server import app
from app.storage.database import init_db, AsyncSessionLocal, engine
from app.storage.models import RequestRecord
from app.storage.events_channel import get_broadcaster
from app.api.routes import normalize_traffic_payload, build_traffic_event_payload


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
    """Ensure database is initialized, records cleared, and broadcaster reset."""
    await init_db()
    async with AsyncSessionLocal() as session:
        await session.execute(delete(RequestRecord))
        await session.commit()

    broadcaster = get_broadcaster()
    broadcaster.clear()
    yield
    broadcaster.clear()


class ASGIStreamTestClient:
    """Helper to drive ASGI streaming requests cleanly without indefinite blocking."""

    def __init__(self, app_instance, path: str = "/api/traffic/stream"):
        self.app = app_instance
        self.path = path
        self.scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "path": path,
            "raw_path": path.encode("utf-8"),
            "query_string": b"",
            "headers": [],
        }
        self.send_queue: asyncio.Queue = asyncio.Queue()
        self.disconnect_event = asyncio.Event()
        self.app_task: asyncio.Task = None

    async def start(self) -> Dict[str, Any]:
        """Start the ASGI app and wait for the http.response.start message."""
        async def receive():
            await self.disconnect_event.wait()
            return {"type": "http.disconnect"}

        async def send(message):
            await self.send_queue.put(message)

        self.app_task = asyncio.create_task(self.app(self.scope, receive, send))

        start_msg = await asyncio.wait_for(self.send_queue.get(), timeout=3.0)
        assert start_msg["type"] == "http.response.start"
        return start_msg

    async def receive_event(self, timeout: float = 3.0) -> Dict[str, Any]:
        """Receive the next SSE body chunk and parse event and data."""
        body_msg = await asyncio.wait_for(self.send_queue.get(), timeout=timeout)
        assert body_msg["type"] == "http.response.body"
        raw_text = body_msg["body"].decode("utf-8")

        parsed = {"event": None, "data": None, "raw": raw_text}
        for line in raw_text.splitlines():
            if line.startswith("event:"):
                parsed["event"] = line[len("event:"):].strip()
            elif line.startswith("data:"):
                parsed["data"] = json.loads(line[len("data:"):].strip())
        return parsed

    async def disconnect(self):
        """Signal client disconnect and wait for the ASGI task to terminate cleanly."""
        if self.disconnect_event and not self.disconnect_event.is_set():
            self.disconnect_event.set()
        if self.app_task:
            await asyncio.wait_for(self.app_task, timeout=3.0)


# =========================================================================
# 1. Effective Route & Redis-Unavailable Fallback Tests
# =========================================================================

@pytest.mark.asyncio
async def test_traffic_stream_returns_200_without_redis():
    """Verify that /api/traffic/stream succeeds with HTTP 200 text/event-stream when Redis is unavailable."""
    client = ASGIStreamTestClient(app)
    try:
        start_msg = await client.start()
        assert start_msg["status"] == 200

        headers = dict(start_msg.get("headers", []))
        content_type = headers.get(b"content-type", b"").decode("utf-8")
        assert "text/event-stream" in content_type
    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_initial_snapshot_sent_when_db_record_exists():
    """Verify that a newly connected client receives the latest RequestRecord as initial snapshot."""
    async with AsyncSessionLocal() as session:
        rec = RequestRecord(
            request_id="req_snap_test_01",
            prompt="Initial snapshot prompt",
            task_type="CODING",
            complexity=0.75,
            selected_model="mock-balanced",
            provider="mock",
            status="SUCCESS",
            total_latency_ms=120.0,
            estimated_cost=0.0003,
        )
        session.add(rec)
        await session.commit()

    client = ASGIStreamTestClient(app)
    try:
        await client.start()
        event_obj = await client.receive_event()

        assert event_obj["event"] == "traffic_event"
        data = event_obj["data"]
        assert set(data.keys()) == EXPECTED_TRAFFIC_FIELDS
        assert data["request_id"] == "req_snap_test_01"
        assert data["prompt"] == "Initial snapshot prompt"
        assert data["selected_model"] == "mock-balanced"
        assert data["total_latency_ms"] == 120.0
    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_no_repeated_database_queries_while_waiting():
    """Verify that the in-memory fallback performs zero database reads after the initial snapshot."""
    async with AsyncSessionLocal() as session:
        rec = RequestRecord(
            request_id="req_query_baseline",
            prompt="Baseline query test",
            task_type="GENERAL_QA",
            selected_model="mock-fast",
            provider="mock",
            status="SUCCESS",
        )
        session.add(rec)
        await session.commit()

    client = ASGIStreamTestClient(app)
    try:
        await client.start()
        # Consume initial snapshot
        await client.receive_event()

        # Track any SQL executed after initial snapshot
        query_count = 0
        def query_listener(conn, cursor, statement, parameters, context, executemany):
            nonlocal query_count
            query_count += 1

        event.listen(engine.sync_engine, "before_cursor_execute", query_listener)
        try:
            broadcaster = get_broadcaster()
            broadcaster.publish_nowait({
                "request_id": "req_live_no_query_1",
                "timestamp": "2026-10-21T14:00:00Z",
                "prompt": "Live event 1",
                "task_type": "GENERAL_QA",
                "complexity": 0.5,
                "selected_model": "mock-fast",
                "provider": "mock",
                "status": "SUCCESS",
                "total_latency_ms": 30.0,
                "estimated_cost": 0.0001,
            })

            live_event = await client.receive_event()
            assert live_event["data"]["request_id"] == "req_live_no_query_1"

            # Must have issued zero SQL queries during live event delivery
            assert query_count == 0, f"Expected 0 queries, got {query_count}"
        finally:
            event.remove(engine.sync_engine, "before_cursor_execute", query_listener)
    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_live_in_memory_event_reaches_connected_client():
    """Verify that an event published to the in-memory broadcaster is yielded to the client."""
    client = ASGIStreamTestClient(app)
    try:
        await client.start()

        broadcaster = get_broadcaster()
        assert broadcaster.subscriber_count == 1

        broadcaster.publish_nowait({
            "request_id": "req_pub_001",
            "timestamp": "2026-10-21T14:15:00Z",
            "prompt": "Published live event",
            "task_type": "CODING",
            "complexity": 0.8,
            "selected_model": "mock-fast",
            "provider": "mock",
            "status": "SUCCESS",
            "total_latency_ms": 55.2,
            "estimated_cost": 0.00025,
        })

        event_obj = await client.receive_event()
        assert event_obj["event"] == "traffic_event"
        assert event_obj["data"]["request_id"] == "req_pub_001"
        assert event_obj["data"]["prompt"] == "Published live event"
    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_two_connected_clients_receive_same_broadcast():
    """Verify that multiple concurrent subscribers both receive the identical broadcast payload."""
    client1 = ASGIStreamTestClient(app)
    client2 = ASGIStreamTestClient(app)
    try:
        await client1.start()
        await client2.start()

        broadcaster = get_broadcaster()
        assert broadcaster.subscriber_count == 2

        payload = {
            "request_id": "req_fanout_broadcast",
            "timestamp": "2026-10-21T14:20:00Z",
            "prompt": "Fanout to 2 clients",
            "task_type": "GENERAL_QA",
            "complexity": 0.4,
            "selected_model": "mock-balanced",
            "provider": "mock",
            "status": "SUCCESS",
            "total_latency_ms": 75.0,
            "estimated_cost": 0.00015,
        }
        broadcaster.publish_nowait(payload)

        evt1 = await client1.receive_event()
        evt2 = await client2.receive_event()

        assert evt1["data"]["request_id"] == "req_fanout_broadcast"
        assert evt2["data"]["request_id"] == "req_fanout_broadcast"
        assert evt1["data"] == evt2["data"]
    finally:
        await client1.disconnect()
        await client2.disconnect()


@pytest.mark.asyncio
async def test_disconnect_cleanup_isolation():
    """Verify that disconnecting one client removes only its queue, leaving other clients active."""
    client1 = ASGIStreamTestClient(app)
    client2 = ASGIStreamTestClient(app)
    try:
        await client1.start()
        await client2.start()

        broadcaster = get_broadcaster()
        assert broadcaster.subscriber_count == 2

        # Disconnect client 1
        await client1.disconnect()
        assert broadcaster.subscriber_count == 1

        # Publish an event; client 2 must still receive it
        broadcaster.publish_nowait({
            "request_id": "req_after_client1_disconnect",
            "timestamp": "2026-10-21T14:25:00Z",
            "prompt": "Client 2 still connected",
            "task_type": "GENERAL_QA",
            "complexity": 0.5,
            "selected_model": "mock-fast",
            "provider": "mock",
            "status": "SUCCESS",
            "total_latency_ms": 40.0,
            "estimated_cost": 0.0001,
        })

        evt2 = await client2.receive_event()
        assert evt2["data"]["request_id"] == "req_after_client1_disconnect"

        # Disconnect client 2
        await client2.disconnect()
        assert broadcaster.subscriber_count == 0
    finally:
        if not client1.disconnect_event.is_set():
            await client1.disconnect()
        if not client2.disconnect_event.is_set():
            await client2.disconnect()


@pytest.mark.asyncio
async def test_snapshot_and_queue_deduplication():
    """Verify that an event emitted in the initial snapshot is not re-emitted if queued concurrently."""
    # Seed a record into DB
    async with AsyncSessionLocal() as session:
        rec = RequestRecord(
            request_id="req_dup_test",
            prompt="Duplicate check prompt",
            task_type="GENERAL_QA",
            selected_model="mock-fast",
            provider="mock",
            status="SUCCESS",
        )
        session.add(rec)
        await session.commit()

    client = ASGIStreamTestClient(app)
    try:
        await client.start()

        # Initial snapshot is received
        snap_evt = await client.receive_event()
        assert snap_evt["data"]["request_id"] == "req_dup_test"

        broadcaster = get_broadcaster()

        # Simulate concurrent publish of the same request_id that was in the snapshot
        broadcaster.publish_nowait({
            "request_id": "req_dup_test",
            "timestamp": "2026-10-21T14:30:00Z",
            "prompt": "Duplicate check prompt",
            "task_type": "GENERAL_QA",
            "complexity": 0.5,
            "selected_model": "mock-fast",
            "provider": "mock",
            "status": "SUCCESS",
            "total_latency_ms": 50.0,
            "estimated_cost": 0.0001,
        })

        # Immediately publish a new distinct event
        broadcaster.publish_nowait({
            "request_id": "req_distinct_next",
            "timestamp": "2026-10-21T14:31:00Z",
            "prompt": "Distinct next prompt",
            "task_type": "CODING",
            "complexity": 0.6,
            "selected_model": "mock-balanced",
            "provider": "mock",
            "status": "SUCCESS",
            "total_latency_ms": 60.0,
            "estimated_cost": 0.0002,
        })

        # Next event received MUST be the distinct event, not the duplicate!
        next_evt = await client.receive_event()
        assert next_evt["data"]["request_id"] == "req_distinct_next"
    finally:
        await client.disconnect()


# =========================================================================
# 2. Redis Pub/Sub Path & Normalization Tests
# =========================================================================

def test_normalize_traffic_payload_with_full_schema():
    """Verify that normalize_traffic_payload preserves a complete 10-field dictionary."""
    raw = {
        "request_id": "req_redis_full",
        "timestamp": "2026-10-21T14:00:00Z",
        "prompt": "Full schema prompt",
        "task_type": "CODING",
        "complexity": 0.9,
        "selected_model": "gpt-4o",
        "provider": "openai",
        "status": "SUCCESS",
        "total_latency_ms": 250.5,
        "estimated_cost": 0.005,
    }
    normalized = normalize_traffic_payload(json.dumps(raw))
    assert normalized == {
        "request_id": "req_redis_full",
        "timestamp": "2026-10-21T14:00:00Z",
        "prompt": "Full schema prompt",
        "task_type": "CODING",
        "complexity": 0.9,
        "selected_model": "gpt-4o",
        "provider": "openai",
        "status": "SUCCESS",
        "total_latency_ms": 250.5,
        "estimated_cost": 0.005,
    }


def test_normalize_traffic_payload_with_log_router_event_schema():
    """Verify that normalize_traffic_payload correctly adapts structured log_router_event payloads."""
    log_event = {
        "event": "request_completed",
        "request_id": "req_redis_log",
        "timestamp": "2026-10-21T14:05:00Z",
        "model": "claude-3-5-sonnet",
        "provider": "anthropic",
        "duration_ms": 312.4,
        "metadata": {
            "tokens": 450,
            "cost": 0.00135,
            "fallback": False,
            "task_type": "CODING",
            "complexity": 0.85,
        },
    }
    normalized = normalize_traffic_payload(json.dumps(log_event))
    assert set(normalized.keys()) == EXPECTED_TRAFFIC_FIELDS
    assert normalized["request_id"] == "req_redis_log"
    assert normalized["selected_model"] == "claude-3-5-sonnet"
    assert normalized["provider"] == "anthropic"
    assert normalized["total_latency_ms"] == 312.4
    assert normalized["estimated_cost"] == 0.00135
    assert normalized["task_type"] == "CODING"


@pytest.mark.asyncio
async def test_redis_pubsub_endpoint_path():
    """Verify that when Redis is available, pubsub events are normalized and yielded as traffic_event."""
    mock_redis = MagicMock()
    mock_pubsub = MagicMock()

    # Create an async generator for pubsub.listen()
    async def mock_listen():
        yield {
            "type": "message",
            "data": json.dumps({
                "request_id": "req_redis_live_01",
                "timestamp": "2026-10-21T14:10:00Z",
                "prompt": "Redis live prompt",
                "task_type": "GENERAL_QA",
                "complexity": 0.5,
                "selected_model": "mock-fast",
                "provider": "mock",
                "status": "SUCCESS",
                "total_latency_ms": 40.0,
                "estimated_cost": 0.0001,
            }),
        }

    mock_pubsub.subscribe = AsyncMock()
    mock_pubsub.unsubscribe = AsyncMock()
    mock_pubsub.close = AsyncMock()
    mock_pubsub.listen = mock_listen
    mock_redis.pubsub.return_value = mock_pubsub

    with patch("app.api.routes.get_redis", return_value=mock_redis):
        client = ASGIStreamTestClient(app)
        try:
            await client.start()
            event_obj = await client.receive_event()

            assert event_obj["event"] == "traffic_event"
            assert event_obj["data"]["request_id"] == "req_redis_live_01"
            assert event_obj["data"]["prompt"] == "Redis live prompt"

            # Check that pubsub subscribe was called
            mock_pubsub.subscribe.assert_awaited_with("traffic_stream")
        finally:
            await client.disconnect()
            # Check that pubsub was cleaned up
            mock_pubsub.unsubscribe.assert_awaited_with("traffic_stream")
            mock_pubsub.close.assert_awaited()
