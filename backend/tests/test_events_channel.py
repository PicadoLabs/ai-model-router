"""
Unit tests for InMemoryTrafficBroadcaster in backend/app/storage/events_channel.py.

Verifies subscriber registration, broadcast delivery, multi-subscriber fan-out,
unsubscription safety, FIFO drop queue-full policy, and concurrency.
"""
import asyncio
import pytest
from typing import Dict, Any

from app.storage.events_channel import (
    InMemoryTrafficBroadcaster,
    get_broadcaster,
)


@pytest.fixture
def broadcaster() -> InMemoryTrafficBroadcaster:
    """Fixture providing a fresh InMemoryTrafficBroadcaster instance for each test."""
    return InMemoryTrafficBroadcaster(default_maxsize=10)


@pytest.mark.asyncio
async def test_single_subscriber_receives_payload(broadcaster: InMemoryTrafficBroadcaster):
    """Verify that a single registered subscriber receives the published payload."""
    queue = broadcaster.subscribe()
    assert broadcaster.subscriber_count == 1

    sample_payload = {
        "request_id": "req-001",
        "task_type": "CODING",
        "selected_model": "mock-fast",
        "status": "SUCCESS",
    }

    delivered = await broadcaster.publish(sample_payload)
    assert delivered == 1
    assert not queue.empty()

    received = await queue.get()
    assert received == sample_payload


@pytest.mark.asyncio
async def test_two_subscribers_receive_same_payload(broadcaster: InMemoryTrafficBroadcaster):
    """Verify that multiple registered subscribers all receive identical copies of the payload."""
    queue1 = broadcaster.subscribe()
    queue2 = broadcaster.subscribe()
    assert broadcaster.subscriber_count == 2

    sample_payload = {
        "request_id": "req-002",
        "prompt": "Write a python function",
        "total_latency_ms": 120.5,
    }

    delivered = await broadcaster.publish(sample_payload)
    assert delivered == 2

    item1 = await queue1.get()
    item2 = await queue2.get()

    assert item1 == sample_payload
    assert item2 == sample_payload
    assert queue1.empty()
    assert queue2.empty()


@pytest.mark.asyncio
async def test_multiple_payloads_arrive_in_order(broadcaster: InMemoryTrafficBroadcaster):
    """Verify that multiple payloads published sequentially arrive in exact FIFO order."""
    queue = broadcaster.subscribe()

    events = [
        {"request_id": f"req-seq-{i}", "seq": i}
        for i in range(5)
    ]

    for event in events:
        broadcaster.publish_nowait(event)

    received_events = []
    for _ in range(5):
        received_events.append(await queue.get())

    assert received_events == events
    assert [e["seq"] for e in received_events] == [0, 1, 2, 3, 4]


@pytest.mark.asyncio
async def test_removed_subscriber_does_not_receive_future_events(broadcaster: InMemoryTrafficBroadcaster):
    """Verify that once a subscriber unsubscribes, it receives no subsequent events."""
    active_queue = broadcaster.subscribe()
    removed_queue = broadcaster.subscribe()
    assert broadcaster.subscriber_count == 2

    # Unsubscribe the second queue
    was_removed = broadcaster.unsubscribe(removed_queue)
    assert was_removed is True
    assert broadcaster.subscriber_count == 1

    payload_after_removal = {"request_id": "req-after-unsub", "event": "active_only"}
    delivered = await broadcaster.publish(payload_after_removal)

    assert delivered == 1
    assert not active_queue.empty()
    assert removed_queue.empty()

    active_item = await active_queue.get()
    assert active_item == payload_after_removal

    # Safe double unsubscription
    second_unsub = broadcaster.unsubscribe(removed_queue)
    assert second_unsub is False


@pytest.mark.asyncio
async def test_queue_full_drops_oldest_event(broadcaster: InMemoryTrafficBroadcaster):
    """
    Verify the queue-full policy: when a bounded queue is full, the oldest unconsumed
    event is dropped to make room for the newest telemetry without blocking the publisher.
    """
    # Create subscriber with tiny capacity of 2
    queue = broadcaster.subscribe(maxsize=2)

    event1 = {"id": "event-1", "data": "oldest"}
    event2 = {"id": "event-2", "data": "middle"}
    event3 = {"id": "event-3", "data": "newest"}

    # Fill queue to capacity (2 items)
    broadcaster.publish_nowait(event1)
    broadcaster.publish_nowait(event2)
    assert queue.full()

    # Publish 3rd event: event1 must be dropped, event2 & event3 retained
    delivered = broadcaster.publish_nowait(event3)
    assert delivered == 1
    assert queue.full()

    # Reading queue should yield event2 then event3 (event1 was dropped)
    first_received = await queue.get()
    second_received = await queue.get()

    assert first_received == event2
    assert second_received == event3
    assert queue.empty()


@pytest.mark.asyncio
async def test_publish_with_no_subscribers_returns_zero(broadcaster: InMemoryTrafficBroadcaster):
    """Verify publishing when no subscribers exist returns 0 and does not raise."""
    assert broadcaster.subscriber_count == 0
    delivered = await broadcaster.publish({"id": "orphan"})
    assert delivered == 0


@pytest.mark.asyncio
async def test_concurrent_publishers_and_consumers(broadcaster: InMemoryTrafficBroadcaster):
    """Verify broadcaster under concurrent publishing and consuming tasks."""
    num_subscribers = 4
    num_events = 20

    queues = [broadcaster.subscribe(maxsize=50) for _ in range(num_subscribers)]

    received_counts = [0] * num_subscribers

    async def consumer(idx: int, q: asyncio.Queue):
        for _ in range(num_events):
            item = await q.get()
            assert "seq" in item
            received_counts[idx] += 1

    consumer_tasks = [
        asyncio.create_task(consumer(i, q))
        for i, q in enumerate(queues)
    ]

    async def publisher(start_idx: int, count: int):
        for j in range(count):
            await broadcaster.publish({"seq": start_idx + j})
            await asyncio.sleep(0.001)

    # Spawn 2 concurrent publishers emitting 10 events each
    pub_task1 = asyncio.create_task(publisher(0, 10))
    pub_task2 = asyncio.create_task(publisher(10, 10))

    await asyncio.gather(pub_task1, pub_task2)
    await asyncio.gather(*consumer_tasks)

    for count in received_counts:
        assert count == num_events


def test_get_broadcaster_singleton():
    """Verify get_broadcaster() returns a persistent singleton instance."""
    b1 = get_broadcaster()
    b2 = get_broadcaster()
    assert b1 is b2
    assert isinstance(b1, InMemoryTrafficBroadcaster)


def test_get_queued_ids(broadcaster: InMemoryTrafficBroadcaster):
    """Verify get_queued_ids returns the set of pending request_ids without modifying the queue."""
    queue = broadcaster.subscribe()
    assert broadcaster.get_queued_ids(queue) == set()

    broadcaster.publish_nowait({"request_id": "req-1", "data": "first"})
    broadcaster.publish_nowait({"request_id": "req-2", "data": "second"})
    broadcaster.publish_nowait({"other_field": "no_id"})

    assert broadcaster.get_queued_ids(queue) == {"req-1", "req-2"}
    # Queue is unconsumed
    assert queue.qsize() == 3

