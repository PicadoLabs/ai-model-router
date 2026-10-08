import time
import asyncio
from collections import deque
from typing import Dict, Tuple, Optional
from fastapi import HTTPException

from app.storage.redis_client import get_redis


class RateLimiter:
    """
    High-performance sliding-window rate limiter supporting both Redis
    and in-memory fallback.
    """

    def __init__(self):
        # In-memory sliding window storage: key -> deque of timestamps
        self._memory_windows: Dict[str, deque] = {}
        self._lock = asyncio.Lock()

    async def check_rate_limit(
        self,
        identifier: str,
        limit_rpm: int,
        window_seconds: int = 60,
    ) -> Tuple[bool, int, int]:
        """
        Evaluates sliding window limit.
        Returns: (is_allowed, remaining_requests, reset_after_seconds)
        """
        if limit_rpm <= 0:
            return True, 999999, 0

        redis = get_redis()
        current_time = time.time()
        window_start = current_time - window_seconds

        if redis:
            try:
                redis_key = f"ratelimit:{identifier}:{window_seconds}"
                pipe = redis.pipeline()
                # Remove expired entries
                pipe.zremrangebyscore(redis_key, 0, window_start)
                # Count current valid entries
                pipe.zcard(redis_key)
                # Add current entry
                pipe.zadd(redis_key, {f"{current_time}": current_time})
                # Set TTL on key
                pipe.expire(redis_key, window_seconds + 5)
                results = await pipe.execute()

                current_count = results[1]
                if current_count >= limit_rpm:
                    # Over limit - roll back current entry addition
                    await redis.zrem(redis_key, f"{current_time}")
                    reset_after = max(1, int(window_seconds))
                    return False, 0, reset_after

                remaining = max(0, limit_rpm - current_count - 1)
                return True, remaining, int(window_seconds)
            except Exception:
                # Fall back to in-memory on any Redis error
                pass

        # In-memory sliding window
        async with self._lock:
            if identifier not in self._memory_windows:
                self._memory_windows[identifier] = deque()

            dq = self._memory_windows[identifier]

            # Pop old timestamps
            while dq and dq[0] <= window_start:
                dq.popleft()

            current_count = len(dq)
            if current_count >= limit_rpm:
                oldest_timestamp = dq[0]
                reset_after = max(1, int(window_seconds - (current_time - oldest_timestamp)))
                return False, 0, reset_after

            # Record current request timestamp
            dq.append(current_time)
            remaining = max(0, limit_rpm - len(dq))
            return True, remaining, int(window_seconds)

    async def enforce_rate_limit(
        self,
        identifier: str,
        limit_rpm: int,
        window_seconds: int = 60,
    ) -> Dict[str, str]:
        """
        Enforces rate limiting. Raises 429 Too Many Requests with standard
        rate-limit headers if quota is exceeded.
        """
        is_allowed, remaining, reset_after = await self.check_rate_limit(
            identifier=identifier,
            limit_rpm=limit_rpm,
            window_seconds=window_seconds,
        )

        headers = {
            "X-RateLimit-Limit": str(limit_rpm),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_after),
        }

        if not is_allowed:
            headers["Retry-After"] = str(reset_after)
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded ({limit_rpm} req/{window_seconds}s). Please retry in {reset_after} seconds.",
                headers=headers,
            )

        return headers

    def clear(self):
        """Clears in-memory state (useful for tests)."""
        self._memory_windows.clear()


rate_limiter = RateLimiter()
