import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from app.storage.database import init_db
from app.observability.metrics import metrics_collector
from app.observability.tracing import router_tracer


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_prometheus_metrics_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Trigger request to populate metrics
        res_gen = await client.post(
            "/api/generate",
            json={"prompt": "Explain Prometheus metrics scraping", "policy": "balanced"},
        )
        assert res_gen.status_code == 200

        # 2. Scrape /metrics
        res_metrics = await client.get("/metrics")
        assert res_metrics.status_code == 200
        text = res_metrics.text
        assert "model_router_requests_total" in text or "model_router_active_requests" in text
        assert "model_router_routing_latency_seconds" in text or "model_router" in text

        # 3. Scrape /api/metrics alias
        res_api_metrics = await client.get("/api/metrics")
        assert res_api_metrics.status_code == 200


def test_metrics_collector_direct_recording():
    metrics_collector.record_request(
        task_type="CODING",
        status="SUCCESS",
        model="mock-fast",
        provider="mock",
        workspace_id="default",
        routing_latency_ms=12.5,
        provider_latency_ms=150.0,
        in_tokens=50,
        out_tokens=100,
        cost=0.0001,
        cost_saved=0.002,
    )
    metrics_collector.set_circuit_breaker("openai", "CLOSED")
    raw_bytes, content_type = metrics_collector.export_metrics()
    assert len(raw_bytes) > 0
    assert "text/plain" in content_type


def test_router_tracer_spans():
    # Sync span
    with router_tracer.start_span("test_sync_stage", {"stage": "analyzer"}) as span:
        pass

    assert span is not None


@pytest.mark.asyncio
async def test_router_async_tracer_spans():
    # Async span
    async with router_tracer.start_async_span("test_async_stage", {"stage": "provider"}) as span:
        pass

    assert span is not None
