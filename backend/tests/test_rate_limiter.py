import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from main import app
from app.auth.rate_limiter import RateLimiter, rate_limiter
from app.storage.database import init_db
from collections import deque
from importlib import import_module


@pytest.fixture
def memory_clock(monkeypatch):
    module = import_module("app.auth.rate_limiter")
    clock = [100.0]
    monkeypatch.setattr(module, "get_redis", lambda: None)
    monkeypatch.setattr(module.time, "time", lambda: clock[0])
    return clock


@pytest.mark.asyncio
async def test_evict_inactive_keys_and_keep_active_limit(memory_clock):
    limiter = RateLimiter()
    await limiter.check_rate_limit("inactive", 1)
    memory_clock[0] = 130.0
    await limiter.check_rate_limit("active", 1)
    memory_clock[0] = 160.0
    assert await limiter.check_rate_limit("active", 1) == (False, 0, 30)
    assert len(limiter._memory_windows) == 1
    assert ("inactive", 60) not in limiter._memory_windows
    assert list(limiter._memory_windows[("active", 60)]) == [130.0]


@pytest.mark.asyncio
async def test_cleanup_respects_each_window_and_empty_keys(memory_clock):
    limiter = RateLimiter()
    await limiter.check_rate_limit("short", 1, 10)
    await limiter.check_rate_limit("long", 1, 120)
    limiter._memory_windows[("empty", 60)] = deque()
    memory_clock[0] = 160.0
    await limiter.check_rate_limit("trigger", 1)
    assert len(limiter._memory_windows) == 2
    assert ("short", 10) not in limiter._memory_windows
    assert ("empty", 60) not in limiter._memory_windows
    assert await limiter.check_rate_limit("long", 1, 120) == (False, 0, 60)
    memory_clock[0] = 220.0
    await limiter.check_rate_limit("trigger", 1)
    assert ("long", 120) not in limiter._memory_windows


@pytest.mark.asyncio
async def test_same_identifier_has_independent_windows(memory_clock):
    limiter = RateLimiter()
    assert (await limiter.check_rate_limit("user", 1, 60))[0]
    assert (await limiter.check_rate_limit("user", 1, 120))[0]
    memory_clock[0] = 160.0
    assert (await limiter.check_rate_limit("user", 1, 60))[0]
    assert not (await limiter.check_rate_limit("user", 1, 120))[0]


@pytest.mark.asyncio
async def test_cleanup_is_periodic_and_clear_resets_it(memory_clock):
    limiter = RateLimiter()
    await limiter.check_rate_limit("short", 1, 10)
    memory_clock[0] = 120.0
    await limiter.check_rate_limit("other", 1)
    assert len(limiter._memory_windows) == 2
    limiter.clear()
    assert limiter._memory_windows == {}


@pytest.mark.asyncio
async def test_concurrent_requests_preserve_limit(memory_clock):
    import asyncio

    limiter = RateLimiter()
    results = await asyncio.gather(*(limiter.check_rate_limit("user", 3) for _ in range(20)))
    assert sum(allowed for allowed, _, _ in results) == 3
    assert sum(len(timestamps) for timestamps in limiter._memory_windows.values()) == 3


@pytest.mark.asyncio
async def test_redis_failure_uses_memory_cleanup(memory_clock, monkeypatch):
    class FailedRedis:
        def pipeline(self):
            raise ConnectionError("unavailable")

    module = import_module("app.auth.rate_limiter")
    monkeypatch.setattr(module, "get_redis", lambda: FailedRedis())
    limiter = RateLimiter()
    await limiter.check_rate_limit("inactive", 1)
    memory_clock[0] = 160.0
    assert (await limiter.check_rate_limit("active", 1))[0]
    assert len(limiter._memory_windows) == 1


@pytest.mark.asyncio
async def test_cleanup_keeps_live_entries_after_clock_rollback(memory_clock):
    limiter = RateLimiter()
    memory_clock[0] = 360.0
    await limiter.check_rate_limit("user", 2, 120)
    memory_clock[0] = 100.0
    await limiter.check_rate_limit("user", 2, 120)
    memory_clock[0] = 420.0
    assert not (await limiter.check_rate_limit("user", 2, 120))[0]


@pytest.fixture(autouse=True)
async def setup_test_state():
    await init_db()
    rate_limiter.clear()


@pytest.mark.asyncio
async def test_in_memory_rate_limiter_unit():
    rl = RateLimiter()
    identifier = "test_user_unit"
    limit = 3

    # First 3 requests should succeed
    for _ in range(limit):
        allowed, remaining, reset_after = await rl.check_rate_limit(identifier, limit_rpm=limit, window_seconds=60)
        assert allowed is True
        assert reset_after > 0

    # 4th request must be blocked
    allowed, remaining, reset_after = await rl.check_rate_limit(identifier, limit_rpm=limit, window_seconds=60)
    assert allowed is False
    assert remaining == 0
    assert reset_after > 0


@pytest.mark.asyncio
async def test_api_rate_limiter_enforcement_429():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        import uuid
        test_ws_id = f"ws-tight-{uuid.uuid4().hex[:6]}"
        # Create a workspace with a strict rate limit (e.g. 2 requests per minute)
        ws_res = await client.post(
            "/api/workspaces",
            json={"id": test_ws_id, "name": "Strict Rate Limit Workspace", "rate_limit_rpm": 2},
        )
        assert ws_res.status_code == 200

        # Create API key for this workspace
        key_res = await client.post(
            "/api/keys",
            json={"name": "Strict Key", "workspace_id": test_ws_id, "rate_limit_rpm": 2},
        )
        assert key_res.status_code == 200
        api_key = key_res.json()["key"]

        # 1st request -> 200
        res1 = await client.post(
            "/api/route",
            json={"prompt": "First request"},
            headers={"X-API-Key": api_key},
        )
        assert res1.status_code == 200

        # 2nd request -> 200
        res2 = await client.post(
            "/api/route",
            json={"prompt": "Second request"},
            headers={"X-API-Key": api_key},
        )
        assert res2.status_code == 200

        # 3rd request -> 429 Too Many Requests
        res3 = await client.post(
            "/api/route",
            json={"prompt": "Third request - should be blocked"},
            headers={"X-API-Key": api_key},
        )
        assert res3.status_code == 429
        assert "Rate limit exceeded" in res3.json()["detail"]
        assert "Retry-After" in res3.headers
        assert res3.headers["X-RateLimit-Limit"] == "2"
        assert res3.headers["X-RateLimit-Remaining"] == "0"



class FakePipeline:
    """Queues commands and runs them on execute(), mimicking  Redis pipeline."""

    def __init__(self, redis: "FakeRedis"):
        self._redis = redis
        self._ops = []

    def zremrangebyscore(self, key, min_score, max_score) -> "FakePipeline":
        self._ops.append(("zremrangebyscore", key, min_score, max_score))
        return self

    def zcard(self, key) -> "FakePipeline":
        self._ops.append(("zcard", key))
        return self

    def zadd(self, key, mapping) -> "FakePipeline":
        self._ops.append(("zadd", key, mapping))
        return self

    def expire(self, key, seconds) -> "FakePipeline":
        self._ops.append(("expire", key, seconds))
        return self

    async def execute(self):
        results = []
        for name, *args in self._ops:
            results.append(getattr(self._redis, f"_{name}")(*args))
        self._ops = []
        return results


class FakeRedis:
    """Minimal sorted-set fake. A repeated member overwrites its score,
    exactly like real Redis, which is what exposes the collision bug."""

    def __init__(self):
        self.data = {}

    def pipeline(self) -> FakePipeline:
        return FakePipeline(self)

    def _zremrangebyscore(self, key, min_score, max_score) -> int:
        zset = self.data.get(key, {})
        stale = [m for m, s in zset.items() if min_score <= s <= max_score]
        for member in stale:
            del zset[member]
        return len(stale)

    def _zcard(self, key) -> int:
        return len(self.data.get(key, {}))

    def _zadd(self, key, mapping: dict) -> int:
        zset = self.data.setdefault(key, {})
        # count total no. of new req in zset
        added = sum(1 for member in mapping if member not in zset)
        zset.update(mapping)
        return added

    def _expire(self, key, seconds) -> bool:
        return True

    async def zrem(self, key, *members) -> int:
        zset = self.data.get(key, {})
        # remove only selected members and return how many it removed
        return sum(1 for member in members if zset.pop(member, None) is not None)

    def members(self, key) -> set[str]:
        return set(self.data.get(key, {}))


REDIS_KEY = "ratelimit:user:60"


@pytest.fixture
def redis_clock(monkeypatch):
    module = import_module("app.auth.rate_limiter")
    fake = FakeRedis()
    clock = [100.0]
    monkeypatch.setattr(module, "get_redis", lambda: fake)
    monkeypatch.setattr(module.time, "time", lambda: clock[0])
    return fake, clock


@pytest.mark.asyncio
async def test_redis_same_timestamp_requests_all_counted(redis_clock):
    fake, _ = redis_clock
    limiter = RateLimiter()
    remaining_values = []
    for _ in range(3):
        allowed, remaining, _ = await limiter.check_rate_limit("user", 5)
        assert allowed is True
        remaining_values.append(remaining)
    assert remaining_values == [4, 3, 2]
    assert len(fake.members(REDIS_KEY)) == 3


@pytest.mark.asyncio
async def test_redis_burst_at_same_timestamp_allows_exactly_limit(redis_clock):
    fake, _ = redis_clock
    limiter = RateLimiter()
    results = await asyncio.gather(*(limiter.check_rate_limit("user", 3) for _ in range(10)))
    assert sum(allowed for allowed, _, _ in results) == 3
    assert len(fake.members(REDIS_KEY)) == 3


@pytest.mark.asyncio
async def test_redis_over_quota_rollback_keeps_other_entries(redis_clock):
    fake, _ = redis_clock
    limiter = RateLimiter()
    for _ in range(3):
        assert (await limiter.check_rate_limit("user", 3))[0]
    members_before = fake.members(REDIS_KEY)
    assert len(members_before) == 3

    allowed, remaining, _ = await limiter.check_rate_limit("user", 3)

    assert allowed is False
    assert remaining == 0
    assert fake.members(REDIS_KEY) == members_before


@pytest.mark.asyncio
async def test_redis_members_are_unique_per_request(redis_clock):
    fake, _ = redis_clock
    limiter = RateLimiter()
    for _ in range(4):
        await limiter.check_rate_limit("user", 10)
    assert len(fake.members(REDIS_KEY)) == 4
