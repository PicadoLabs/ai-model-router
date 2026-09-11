import json
import pytest
from typer.testing import CliRunner
from app.cli.main import app

runner = CliRunner()

def test_cli_doctor_json():
    result = runner.invoke(app, ["doctor", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "python" in data
    assert "database" in data
    assert "mock_engine" in data

def test_cli_models_json():
    result = runner.invoke(app, ["models", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    if len(data) > 0:
        assert "id" in data[0]
        assert "provider" in data[0]

def test_cli_route_json():
    result = runner.invoke(app, ["route", "test prompt", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "selected_model" in data
    assert "estimated_latency_ms" in data

def test_cli_run_json():
    result = runner.invoke(app, ["run", "test prompt", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "decision" in data
    assert "response" in data
    assert "fallback" in data

def test_cli_analytics_json():
    result = runner.invoke(app, ["analytics", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "total_requests" in data
    assert "avg_latency_ms" in data
    assert "savings" in data
