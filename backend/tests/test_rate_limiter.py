import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from app.auth.rate_limiter import RateLimiter, rate_limiter
from app.storage.database import init_db


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
