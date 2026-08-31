import pytest
from app.models.schemas import ModelMetadata, ModelTier, RequestAnalysis, TaskType, PriorityLevel
from app.router.scoring import filter_candidate_models, compute_candidate_score
from app.router.engine import route_request


@pytest.fixture
def sample_models():
    return [
        ModelMetadata(
            id="mock-fast",
            name="Mock Fast",
            provider="mock",
            tier=ModelTier.FAST,
            context_window=8192,
            supports_coding=True,
            supports_reasoning=False,
            quality_score=0.75,
            speed_score=0.98,
            cost_per_input_token=0.0,
            cost_per_output_token=0.0,
        ),
        ModelMetadata(
            id="mock-power",
            name="Mock Power",
            provider="mock",
            tier=ModelTier.POWER,
            context_window=128000,
            supports_coding=True,
            supports_reasoning=True,
            quality_score=0.98,
            speed_score=0.60,
            cost_per_input_token=0.000005,
            cost_per_output_token=0.000015,
        ),
    ]


def test_candidate_filtering_context_overflow(sample_models):
    large_analysis = RequestAnalysis(
        task_type=TaskType.LONG_CONTEXT,
        complexity=0.7,
        context_size=15000,  # exceeds mock-fast 8192
    )
    eligible, rejected = filter_candidate_models(sample_models, large_analysis)
    assert len(eligible) == 1
    assert eligible[0].id == "mock-power"
    assert "mock-fast" in rejected


def test_scoring_weights(sample_models):
    analysis = RequestAnalysis(
        task_type=TaskType.CODING,
        complexity=0.3,
        latency_priority=PriorityLevel.HIGH,
        cost_sensitivity=PriorityLevel.HIGH,
    )
    weights = {"quality_weight": 0.1, "cost_weight": 0.5, "speed_weight": 0.4, "capability_weight": 0.0, "reliability_weight": 0.0}
    score_fast = compute_candidate_score(sample_models[0], analysis, weights)
    score_power = compute_candidate_score(sample_models[1], analysis, weights)
    assert score_fast.overall_score > score_power.overall_score


def test_routing_decision_explainability(sample_models):
    analysis = RequestAnalysis(
        task_type=TaskType.DEBUGGING,
        complexity=0.85,
        complexity_label=PriorityLevel.HIGH,
        reasoning_required=True,
        coding_required=True,
        quality_requirement=PriorityLevel.HIGH,
    )
    weights = {"quality_weight": 0.6, "cost_weight": 0.1, "speed_weight": 0.1, "capability_weight": 0.1, "reliability_weight": 0.1}
    decision = route_request(analysis, sample_models, weights, policy_name="highest_quality")
    assert decision.selected_model == "mock-power"
    assert decision.confidence > 0.70
    assert len(decision.reasons) > 0
    assert any("DEBUGGING" in r for r in decision.reasons)
