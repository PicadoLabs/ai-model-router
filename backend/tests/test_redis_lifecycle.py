"""
Unit and integration tests for Redis lifecycle and end-to-end traffic event routing.

Verifies:
1. Redis initialization during application startup lifespan.
2. Graceful resilience when Redis is unreachable or unconfigured (fallback remains active).
3. Redis client connection cleanup during application shutdown.
4. End-to-end Redis event publishing from /api/generate with fault isolation.
5. End-to-end in-memory fallback delivery without Redis.
6. Snapshot and in-memory queue ordering during concurrent commits.
"""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import AsyncClient, ASGITransport

from sqlalchemy import delete
from app.server import app, lifespan
from app.config.settings import get_settings
from app.storage.database import init_db, AsyncSessionLocal
from app.storage.models import RequestRecord
from app.storage.redis_client import init_redis, close_redis, get_redis, publish_traffic_event
from app.storage.events_channel import get_broadcaster
from tests.test_traffic_sse import ASGIStreamTestClient


@pytest.fixture(autouse=True)
async def cleanup_environment():
    """Reset Redis, database records, and broadcaster state before and after each test."""
    await init_db()
    async with AsyncSessionLocal() as session:
        await session.execute(delete(RequestRecord))
        await session.commit()
    await close_redis()
    broadcaster = get_broadcaster()
    broadcaster.clear()
    yield
    await close_redis()
    broadcaster.clear()


# =========================================================================
# 1. Lifespan Startup and Shutdown Tests
# =========================================================================

@pytest.mark.asyncio
async def test_redis_initialization_on_app_startup():
    """Verify that Redis initializes during application lifespan when REDIS_URL is configured."""
    mock_redis = MagicMock()
    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.close = AsyncMock()

    settings = get_settings()
    with patch.object(settings, "REDIS_URL", "redis://mock-redis:6379/0"):
        with patch("redis.asyncio.from_url", return_value=mock_redis) as mock_from_url:
            async with lifespan(app):
                # Redis should be initialized and reachable
                mock_from_url.assert_called_once_with("redis://mock-redis:6379/0", decode_responses=True)
                mock_redis.ping.assert_awaited_once()
                assert get_redis() is mock_redis

            # On shutdown, Redis client should be closed and reset to None
            mock_redis.close.assert_awaited_once()
            assert get_redis() is None


@pytest.mark.asyncio
async def test_redis_initialization_failure_resilience():
    """Verify that if Redis ping/connection fails on startup, the app still starts and get_redis() is None."""
    settings = get_settings()
    with patch.object(settings, "REDIS_URL", "redis://unreachable:6379/0"):
        with patch("redis.asyncio.from_url", side_effect=ConnectionError("Could not connect to Redis")):
            async with lifespan(app):
                # Application startup must NOT fail; Redis falls back to None
                assert get_redis() is None

            # Shutdown should execute cleanly without error
            assert get_redis() is None


@pytest.mark.asyncio
async def test_redis_unconfigured_runs_in_memory():
    """Verify that when REDIS_URL is empty, lifespan startup proceeds with get_redis() as None."""
    settings = get_settings()
    with patch.object(settings, "REDIS_URL", ""):
        async with lifespan(app):
            assert get_redis() is None


@pytest.mark.asyncio
async def test_close_redis_idempotent_and_safe():
    """Verify that close_redis handles exceptions and resets client state to None."""
    mock_redis = MagicMock()
    mock_redis.close = AsyncMock(side_effect=RuntimeError("Socket error on close"))

    with patch("app.storage.redis_client._redis_client", mock_redis):
        # Should not raise exception
        await close_redis()
        assert get_redis() is None


# =========================================================================
# 2. End-to-End Publishing & Fault Tolerance Tests
# =========================================================================

@pytest.mark.asyncio
async def test_end_to_end_redis_publishing_from_generate():
    """Verify that successful /api/generate requests publish events to Redis channel 'traffic_stream'."""
    mock_redis = MagicMock()
    published_event = asyncio.Event()

    async def mock_publish(channel, raw_payload):
        published_event.set()

    mock_redis.publish = AsyncMock(side_effect=mock_publish)

    with patch("app.storage.redis_client._redis_client", mock_redis):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                "/api/generate",
                json={"prompt": "Test Redis publishing path", "policy": "balanced"},
            )
            assert res.status_code == 200
            req_id = res.json()["request_id"]

        # Deterministic wait for async publishing task
        await asyncio.wait_for(published_event.wait(), timeout=3.0)

        assert mock_redis.publish.await_count >= 1
        call_args = mock_redis.publish.await_args_list[0]
        channel, raw_payload = call_args.args

        assert channel == "traffic_stream"
        payload_data = json.loads(raw_payload)
        assert payload_data["request_id"] == req_id
        assert "event" in payload_data


@pytest.mark.asyncio
async def test_redis_publishing_error_does_not_fail_request():
    """Verify that a Redis publish failure does not cause /api/generate to fail or raise an error."""
    mock_redis = MagicMock()
    mock_redis.publish = AsyncMock(side_effect=ConnectionError("Redis connection dropped"))

    with patch("app.storage.redis_client._redis_client", mock_redis):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                "/api/generate",
                json={"prompt": "Test Redis failure tolerance", "policy": "balanced"},
            )
            # Request MUST succeed despite Redis publish error
            assert res.status_code == 200
            assert "response" in res.json()


# =========================================================================
# 3. End-to-End In-Memory Fallback & Snapshot Ordering Tests
# =========================================================================

@pytest.mark.asyncio
async def test_end_to_end_in_memory_fallback_generate_to_stream():
    """Verify that /api/generate delivers live events to /api/traffic/stream when Redis is unavailable."""
    assert get_redis() is None

    client = ASGIStreamTestClient(app)
    try:
        await client.start()

        # Execute generate request
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as http_client:
            res = await http_client.post(
                "/api/generate",
                json={"prompt": "Live traffic e2e message", "policy": "balanced"},
            )
            assert res.status_code == 200
            req_id = res.json()["request_id"]

        # Receive SSE event on connected stream client
        event_obj = await client.receive_event()
        assert event_obj["event"] == "traffic_event"
        assert event_obj["data"]["request_id"] == req_id
        assert event_obj["data"]["prompt"] == "Live traffic e2e message"
    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_snapshot_ordering_when_event_queued_during_snapshot():
    """
    Verify regression: if a request is queued while the initial snapshot is being queried,
    events are emitted through the actual generator in exact chronological order without duplicate.
    """
    # Seed DB with initial record
    async with AsyncSessionLocal() as session:
        rec1 = RequestRecord(
            request_id="req_order_1",
            prompt="First prompt",
            task_type="GENERAL_QA",
            selected_model="mock-fast",
            provider="mock",
            status="SUCCESS",
        )
        session.add(rec1)
        await session.commit()

    from sqlalchemy.ext.asyncio import AsyncSession
    orig_execute = AsyncSession.execute

    async def execute_hook(self, *args, **kwargs):
        res = await orig_execute(self, *args, **kwargs)
        # When snapshot executes its SELECT, deposit req_order_1 and req_order_2 into broadcaster
        if args and "requests" in str(args[0]).lower():
            broadcaster = get_broadcaster()
            broadcaster.publish_nowait({
                "request_id": "req_order_1",
                "timestamp": "2026-10-21T14:40:00Z",
                "prompt": "First prompt",
                "task_type": "GENERAL_QA",
                "complexity": 0.5,
                "selected_model": "mock-fast",
                "provider": "mock",
                "status": "SUCCESS",
                "total_latency_ms": 30.0,
                "estimated_cost": 0.0001,
            })
            broadcaster.publish_nowait({
                "request_id": "req_order_2",
                "timestamp": "2026-10-21T14:41:00Z",
                "prompt": "Second prompt",
                "task_type": "CODING",
                "complexity": 0.7,
                "selected_model": "mock-balanced",
                "provider": "mock",
                "status": "SUCCESS",
                "total_latency_ms": 60.0,
                "estimated_cost": 0.0003,
            })
        return res

    with patch.object(AsyncSession, "execute", new=execute_hook):
        from app.api.routes import traffic_stream
        resp = await traffic_stream()
        gen = resp.body_iterator

        first_evt = await gen.__anext__()
        second_evt = await gen.__anext__()
        await gen.aclose()

        item1 = json.loads(first_evt["data"])
        item2 = json.loads(second_evt["data"])

        # Must be in exact chronological order without duplicating req_order_1
        assert item1["request_id"] == "req_order_1"
        assert item2["request_id"] == "req_order_2"


@pytest.mark.asyncio
async def test_redis_runtime_disconnection_falls_back_to_in_memory():
    """Verify that if Redis disconnects mid-stream, the endpoint switches to in-memory without crashing."""
    mock_redis = MagicMock()
    mock_pubsub = MagicMock()

    async def mock_listen():
        yield {
            "type": "message",
            "data": json.dumps({
                "request_id": "req_redis_before_disconnect",
                "timestamp": "2026-10-21T14:50:00Z",
                "prompt": "Redis initial prompt",
                "task_type": "GENERAL_QA",
                "complexity": 0.5,
                "selected_model": "mock-fast",
                "provider": "mock",
                "status": "SUCCESS",
                "total_latency_ms": 40.0,
                "estimated_cost": 0.0001,
            }),
        }
        # Simulate network drop
        raise ConnectionError("Lost connection to Redis")

    mock_pubsub.subscribe = AsyncMock()
    mock_pubsub.unsubscribe = AsyncMock()
    mock_pubsub.close = AsyncMock()
    mock_pubsub.listen = mock_listen
    mock_redis.pubsub.return_value = mock_pubsub

    with patch("app.api.routes.get_redis", return_value=mock_redis):
        client = ASGIStreamTestClient(app)
        try:
            await client.start()
            # 1. Event from Redis before disconnect
            evt1 = await client.receive_event()
            assert evt1["data"]["request_id"] == "req_redis_before_disconnect"

            # 2. Redis dropped, fallback to in-memory. Publish in-memory event:
            broadcaster = get_broadcaster()
            broadcaster.publish_nowait({
                "request_id": "req_in_memory_after_redis_drop",
                "timestamp": "2026-10-21T14:51:00Z",
                "prompt": "In-memory prompt after drop",
                "task_type": "CODING",
                "complexity": 0.6,
                "selected_model": "mock-fast",
                "provider": "mock",
                "status": "SUCCESS",
                "total_latency_ms": 50.0,
                "estimated_cost": 0.0002,
            })

            # 3. Client receives the in-memory event seamlessly
            evt2 = await client.receive_event()
            assert evt2["data"]["request_id"] == "req_in_memory_after_redis_drop"
        finally:
            await client.disconnect()


@pytest.mark.asyncio
async def test_multiple_events_arriving_during_snapshot_ordered_and_deduplicated():
    """
    Verify that when multiple events arrive in the subscriber's queue during the initial
    snapshot query, they are delivered in strict FIFO order, without duplicates and without
    dropping events.
    """
    broadcaster = get_broadcaster()
    broadcaster.clear()

    async with AsyncSessionLocal() as session:
        # DB already has an initial baseline record
        rec0 = RequestRecord(
            request_id="req_base_0",
            prompt="Baseline prompt",
            task_type="GENERAL_QA",
            selected_model="mock-fast",
            provider="mock",
            status="SUCCESS",
        )
        session.add(rec0)
        await session.commit()

    from sqlalchemy.ext.asyncio import AsyncSession
    orig_execute = AsyncSession.execute

    async def execute_hook(self, *args, **kwargs):
        res = await orig_execute(self, *args, **kwargs)
        if args and "requests" in str(args[0]).lower():
            # While snapshot query runs, 3 distinct events arrive in the queue
            broadcaster = get_broadcaster()
            for i in [1, 2, 3]:
                broadcaster.publish_nowait({
                    "request_id": f"req_multi_{i}",
                    "timestamp": f"2026-10-21T14:4{i}:00Z",
                    "prompt": f"Prompt {i}",
                    "task_type": "GENERAL_QA",
                    "complexity": 0.5,
                    "selected_model": "mock-fast",
                    "provider": "mock",
                    "status": "SUCCESS",
                    "total_latency_ms": 30.0 + i,
                    "estimated_cost": 0.0001 * i,
                })
        return res

    with patch.object(AsyncSession, "execute", new=execute_hook):
        from app.api.routes import traffic_stream
        resp = await traffic_stream()
        gen = resp.body_iterator

        # We expect req_base_0 (the snapshot), then req_multi_1, req_multi_2, req_multi_3 in order
        events = []
        for _ in range(4):
            evt = await gen.__anext__()
            events.append(json.loads(evt["data"])["request_id"])
        await gen.aclose()

        assert events == ["req_base_0", "req_multi_1", "req_multi_2", "req_multi_3"]


@pytest.mark.asyncio
async def test_multiple_events_during_snapshot_where_db_returns_latest_queued_event():
    """
    Verify that if the snapshot query returns a record that is already queued (e.g. req_multi_3),
    the duplicate snapshot is suppressed and all queued events are yielded in exact order.
    """
    broadcaster = get_broadcaster()
    broadcaster.clear()

    async with AsyncSessionLocal() as session:
        # Pre-seed record 3 as the latest committed DB record
        rec3 = RequestRecord(
            request_id="req_multi_3",
            prompt="Prompt 3",
            task_type="GENERAL_QA",
            selected_model="mock-fast",
            provider="mock",
            status="SUCCESS",
        )
        session.add(rec3)
        await session.commit()

    from sqlalchemy.ext.asyncio import AsyncSession
    orig_execute = AsyncSession.execute

    async def execute_hook(self, *args, **kwargs):
        res = await orig_execute(self, *args, **kwargs)
        if args and "requests" in str(args[0]).lower():
            # While snapshot executes, req_multi_1, req_multi_2, req_multi_3 are queued
            broadcaster = get_broadcaster()
            for i in [1, 2, 3]:
                broadcaster.publish_nowait({
                    "request_id": f"req_multi_{i}",
                    "timestamp": f"2026-10-21T14:4{i}:00Z",
                    "prompt": f"Prompt {i}",
                    "task_type": "GENERAL_QA",
                    "complexity": 0.5,
                    "selected_model": "mock-fast",
                    "provider": "mock",
                    "status": "SUCCESS",
                    "total_latency_ms": 30.0 + i,
                    "estimated_cost": 0.0001 * i,
                })
        return res

    with patch.object(AsyncSession, "execute", new=execute_hook):
        from app.api.routes import traffic_stream
        resp = await traffic_stream()
        gen = resp.body_iterator

        events = []
        for _ in range(3):
            evt = await gen.__anext__()
            events.append(json.loads(evt["data"])["request_id"])
        await gen.aclose()

        # Must not emit req_multi_3 first; must emit 1, 2, 3 in order without duplicate
        assert events == ["req_multi_1", "req_multi_2", "req_multi_3"]

