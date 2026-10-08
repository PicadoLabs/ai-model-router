import pytest
import os
import json
import tempfile
from typer.testing import CliRunner
from httpx import AsyncClient, ASGITransport
from main import app
from app.experiments.benchmark import (
    BenchmarkRunner,
    CandidateEvaluation,
    extract_numeric_answer,
    extract_python_code,
    evaluate_response_correctness,
    calculate_pareto_frontier,
    generate_ascii_pareto_chart,
)
from app.cli.main import app as cli_app

runner = CliRunner()


def test_extract_numeric_answer():
    assert extract_numeric_answer("The final answer is #### 72") == 72.0
    assert extract_numeric_answer("Result: \\boxed{10.5}") == 10.5
    assert extract_numeric_answer("Therefore, Sarah gets 5 dollars back.") == 5.0
    assert extract_numeric_answer("No numbers here") is None


def test_extract_python_code():
    md_code = "```python\ndef add(a, b):\n    return a + b\n```"
    assert extract_python_code(md_code) == "def add(a, b):\n    return a + b"
    
    plain_code = "def multiply(x, y):\n    return x * y"
    assert "def multiply" in extract_python_code(plain_code)


def test_evaluate_response_correctness_math():
    sample = {"id": "m1", "task_type": "MATH", "expected_number": 42.0}
    is_corr, score = evaluate_response_correctness("MATH", "The answer is #### 42", sample)
    assert is_corr is True
    assert score == 1.0

    is_corr_wrong, _ = evaluate_response_correctness("MATH", "The answer is #### 100", sample, is_mock=False)
    assert is_corr_wrong is False


def test_evaluate_response_correctness_code():
    sample = {
        "id": "c1",
        "task_type": "CODE",
        "test_code": "assert add(2, 3) == 5\nassert add(0, 0) == 0",
    }
    good_code = "def add(a, b):\n    return a + b"
    is_corr, score = evaluate_response_correctness("CODE", good_code, sample, is_mock=False)
    assert is_corr is True
    assert score == 1.0

    bad_code = "def add(a, b):\n    return a - b"
    is_corr_bad, _ = evaluate_response_correctness("CODE", bad_code, sample, is_mock=False)
    assert is_corr_bad is False


def test_pareto_frontier_calculation():
    candidates = [
        # Candidate 1: High accuracy (95%), High cost ($1.00), High latency (200ms) -> Non-dominated (highest accuracy)
        CandidateEvaluation(
            name="frontier-accuracy",
            target_type="model",
            total_samples=10,
            correct_samples=9,
            accuracy_percent=95.0,
            avg_latency_ms=200.0,
            p95_latency_ms=250.0,
            avg_cost_per_1k_usd=1.00,
            total_cost_usd=0.01,
        ),
        # Candidate 2: Medium accuracy (90%), Ultra-low cost ($0.05), Low latency (50ms) -> Non-dominated (cheapest/fastest)
        CandidateEvaluation(
            name="frontier-cost-speed",
            target_type="model",
            total_samples=10,
            correct_samples=9,
            accuracy_percent=90.0,
            avg_latency_ms=50.0,
            p95_latency_ms=60.0,
            avg_cost_per_1k_usd=0.05,
            total_cost_usd=0.0005,
        ),
        # Candidate 3: Low accuracy (80%), High cost ($1.50), High latency (300ms) -> Dominated by Candidate 1 & 2
        CandidateEvaluation(
            name="dominated-slow-expensive",
            target_type="model",
            total_samples=10,
            correct_samples=8,
            accuracy_percent=80.0,
            avg_latency_ms=300.0,
            p95_latency_ms=350.0,
            avg_cost_per_1k_usd=1.50,
            total_cost_usd=0.015,
        ),
    ]

    pareto_names = calculate_pareto_frontier(candidates)
    assert "frontier-accuracy" in pareto_names
    assert "frontier-cost-speed" in pareto_names
    assert "dominated-slow-expensive" not in pareto_names

    chart = generate_ascii_pareto_chart(candidates)
    assert "Acc (%)" in chart
    assert "Cost ($/1K)" in chart


@pytest.mark.asyncio
async def test_benchmark_runner_execution():
    bench = BenchmarkRunner()
    report = await bench.run_benchmark(
        dataset_name="gsm8k",
        limit=2,
        policies_to_test=["balanced"],
        models_to_test=["gpt-4o", "gpt-4o-mini"],
        baseline_model="gpt-4o",
    )

    assert report.dataset_name.startswith("GSM8K")
    assert report.sample_count == 2
    assert report.baseline_model == "gpt-4o"
    assert len(report.candidates) >= 2
    assert len(report.pareto_frontier) >= 1
    assert report.ascii_graph != ""


@pytest.mark.asyncio
async def test_benchmark_api_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Datasets endpoint
        r_ds = await ac.get("/api/benchmarks/datasets")
        assert r_ds.status_code == 200
        datasets = r_ds.json().get("datasets", [])
        assert any(d["id"] == "gsm8k" for d in datasets)
        assert any(d["id"] == "humaneval" for d in datasets)

        # 2. Run benchmark endpoint
        r_run = await ac.post("/api/benchmarks/run", json={
            "dataset": "gsm8k",
            "limit": 2,
            "policies": ["balanced"],
            "models": ["gpt-4o"],
            "baseline_model": "gpt-4o",
        })
        assert r_run.status_code == 200
        data = r_run.json()
        assert data["sample_count"] == 2
        assert "pareto_frontier" in data


def test_benchmark_cli_command():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_json = os.path.join(tmpdir, "bench_out.json")
        res = runner.invoke(cli_app, [
            "benchmark",
            "--dataset", "gsm8k",
            "--limit", "2",
            "--policy", "balanced",
            "--format", "json",
            "--output", out_json,
        ])
        assert res.exit_code == 0
        assert os.path.exists(out_json)
        with open(out_json, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
            assert "pareto_frontier" in saved_data
