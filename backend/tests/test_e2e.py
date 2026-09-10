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


@pytest.mark.asyncio
async def test_api_traffic_export_json_contains_audit_fields():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        generate_res = await client.post(
            "/api/generate",
            json={"prompt": "Write a Python function for a traffic export"},
        )
        assert generate_res.status_code == 200

        export_res = await client.get("/api/traffic/export?format=json")

    assert export_res.status_code == 200
    assert export_res.headers["content-type"].startswith("application/json")
    assert "attachment" in export_res.headers["content-disposition"]
    records = export_res.json()
    assert records
    assert {
        "timestamp",
        "request_id",
        "prompt_preview",
        "task_type",
        "complexity",
        "selected_model",
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "cost_saved",
        "total_latency_ms",
    }.issubset(records[0])


@pytest.mark.asyncio
async def test_api_traffic_export_csv_returns_downloadable_rows():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        generate_res = await client.post(
            "/api/generate",
            json={"prompt": "Summarize this traffic record"},
        )
        assert generate_res.status_code == 200

        export_res = await client.get("/api/traffic/export?format=csv")

    assert export_res.status_code == 200
    assert export_res.headers["content-type"].startswith("text/csv")
    assert "traffic-export.csv" in export_res.headers["content-disposition"]
    lines = export_res.text.splitlines()
    assert lines[0].startswith("timestamp,request_id,prompt_preview,")
    assert len(lines) >= 2


@pytest.mark.asyncio
async def test_api_traffic_export_rejects_unknown_format():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        export_res = await client.get("/api/traffic/export?format=xml")

    assert export_res.status_code == 422
