import time
import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from app.analyzer.semantic_classifier import SemanticEmbeddingClassifier, semantic_classifier
from app.models.schemas import TaskType
from app.storage.database import init_db


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


def test_semantic_classifier_direct():
    classifier = SemanticEmbeddingClassifier()

    # Ambiguous coding prompt lacking exact regex "write a python function"
    coding_res = classifier.classify("Can you show me how to design an interface for database transactions in backend services?")
    assert coding_res.task_type in [TaskType.CODING, TaskType.ANALYSIS]
    assert coding_res.coding_required is True

    # Ambiguous debugging prompt
    debug_res = classifier.classify("Our team is facing a defect where memory leaks cause unhandled defect panics during load")
    assert debug_res.task_type == TaskType.DEBUGGING
    assert debug_res.reasoning_required is True

    # Summarization prompt
    sum_res = classifier.classify("Please provide a brief digest outlining the mainideas and bulletpoints of this document")
    assert sum_res.task_type == TaskType.SUMMARIZATION

    # Math prompt
    math_res = classifier.classify("Solve this matrix polynomial eigenvalue variance equation")
    assert math_res.task_type == TaskType.MATH


def test_semantic_classifier_latency_under_10ms():
    """Verify execution overhead is strictly under 10ms."""
    sample_prompts = [
        "How do I structure a microservice architecture with async queue workers?",
        "Explain the causal implications and tradeoffs between SQL and NoSQL databases",
        "Parse the unstructured table and convert into schema entities format",
        "Translate this greeting phrase into french and german dialects",
        "What is the capital of Japan?",
    ]

    for p in sample_prompts:
        t0 = time.perf_counter()
        res = semantic_classifier.classify(p)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        assert elapsed_ms < 10.0, f"Classifier exceeded 10ms threshold: {elapsed_ms:.2f}ms"
        assert res.task_type is not None


@pytest.mark.asyncio
async def test_api_route_with_semantic_analyzer_mode():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "prompt": "Investigate rootcause of flaky unhandled panic in worker",
            "analyzer_mode": "semantic",
            "policy": "balanced",
        }
        res = await client.post("/api/route", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["analysis"]["task_type"] == "DEBUGGING"
        assert data["analysis"]["analyzer_used"] in ["semantic_embedding", "semantic_onnx"]
