import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from app.storage.database import init_db


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_api_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_api_route_only():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"prompt": "Write a Python script to benchmark models", "policy": "balanced"}
        res = await client.post("/api/route", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "decision" in data
        assert "analysis" in data
        assert data["analysis"]["task_type"] == "CODING"


@pytest.mark.asyncio
async def test_api_generate_end_to_end():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"prompt": "Debug this memory leak in python subprocess", "policy": "balanced"}
        res = await client.post("/api/generate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "response" in data
        assert "metrics" in data
        assert len(data["response"]["content"]) > 0


@pytest.mark.asyncio
async def test_api_models_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/models")
        assert res.status_code == 200
        models = res.json()
        assert len(models) >= 3


@pytest.mark.asyncio
async def test_api_analytics():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/analytics")
        assert res.status_code == 200
        data = res.json()
        assert "total_requests" in data
        assert "savings" in data
