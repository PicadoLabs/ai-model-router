"""
In-memory event channel for live SSE traffic stream broadcasting.

Provides a fan-out pub/sub mechanism decoupling request persistence
from SSE stream consumers without database polling.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("model_router.events_channel")


class InMemoryTrafficBroadcaster:
    """
    In-memory publisher-subscriber broadcaster for routing traffic events.

    Each subscriber is assigned a bounded asyncio.Queue.
    When a queue is full, the oldest unconsumed event is discarded
    to accommodate the newest telemetry without blocking the publisher
    or causing unbounded memory growth.
    """

    def __init__(self, default_maxsize: int = 100):
        self._default_maxsize = default_maxsize
        self._subscribers: Set[asyncio.Queue] = set()

    @property
    def subscriber_count(self) -> int:
        """Return the number of currently active subscribers."""
        return len(self._subscribers)

    def subscribe(self, maxsize: Optional[int] = None) -> asyncio.Queue:
        """
        Register a new subscriber and return its dedicated bounded queue.

        Args:
            maxsize: Optional custom maximum queue size. Defaults to default_maxsize.

        Returns:
            asyncio.Queue dedicated to the new subscriber.
        """
        queue_size = maxsize if maxsize is not None else self._default_maxsize
        queue: asyncio.Queue = asyncio.Queue(maxsize=queue_size)
        self._subscribers.add(queue)
        logger.debug("Subscriber registered. Active subscribers: %d", len(self._subscribers))
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> bool:
        """
        Unregister a subscriber queue safely.

        Args:
            queue: The subscriber queue to remove.

        Returns:
            True if the queue was present and removed, False otherwise.
        """
        existed = queue in self._subscribers
        self._subscribers.discard(queue)
        if existed:
            logger.debug("Subscriber unregistered. Active subscribers: %d", len(self._subscribers))
        return existed

    def get_queued_ids(self, queue: asyncio.Queue) -> Set[str]:
        """
        Safely inspect request IDs currently queued for a subscriber
        without consuming events from the queue.

        Args:
            queue: The subscriber queue to inspect.

        Returns:
            A set of request_id strings present in the queue.
        """
        raw_deque = getattr(queue, "_queue", None)
        if not raw_deque:
            return set()
        return {
            item.get("request_id")
            for item in raw_deque
            if isinstance(item, dict) and item.get("request_id")
        }

    def publish_nowait(self, payload: Dict[str, Any]) -> int:
        """
        Publish an event payload to all currently registered subscribers synchronously.

        If a subscriber's queue is full, the oldest event in that queue is discarded
        (FIFO drop) to ensure the newest telemetry is delivered without stalling publishers.

        Args:
            payload: Event dictionary to broadcast.

        Returns:
            The number of subscribers successfully queued for delivery.
        """
        if not self._subscribers:
            return 0

        delivered_count = 0
        # Snapshot the set to ensure thread/coroutine safe iteration
        subscribers_snapshot: List[asyncio.Queue] = list(self._subscribers)

        for queue in subscribers_snapshot:
            # Check if subscriber was removed concurrently
            if queue not in self._subscribers:
                continue

            try:
                queue.put_nowait(payload)
                delivered_count += 1
            except asyncio.QueueFull:
                # Queue-full policy: Drop the oldest event to make room for newest telemetry
                try:
                    queue.get_nowait()
                except (asyncio.QueueEmpty, ValueError):
                    pass

                try:
                    queue.put_nowait(payload)
                    delivered_count += 1
                except asyncio.QueueFull:
                    # Extremely rare race: skip if still full
                    pass

                logger.warning(
                    "Subscriber queue full (maxsize=%d); dropped oldest event to queue newest.",
                    queue.maxsize,
                )

        return delivered_count

    async def publish(self, payload: Dict[str, Any]) -> int:
        """
        Asynchronously publish an event payload to all subscribers.

        Args:
            payload: Event dictionary to broadcast.

        Returns:
            The number of subscribers successfully queued for delivery.
        """
        return self.publish_nowait(payload)

    async def broadcast(self, payload: Dict[str, Any]) -> int:
        """Alias for publish()."""
        return self.publish_nowait(payload)

    def clear(self) -> None:
        """Remove all active subscribers. Useful for test teardown."""
        self._subscribers.clear()


# Global singleton instance
_broadcaster: Optional[InMemoryTrafficBroadcaster] = None


def get_broadcaster() -> InMemoryTrafficBroadcaster:
    """Return the global InMemoryTrafficBroadcaster singleton."""
    global _broadcaster
    if _broadcaster is None:
        _broadcaster = InMemoryTrafficBroadcaster()
    return _broadcaster
