from typing import List, Dict, Tuple, Optional
from app.models.schemas import ModelMetadata, RequestAnalysis, CandidateScore, PriorityLevel


def filter_candidate_models(
    models: List[ModelMetadata],
    analysis: RequestAnalysis,
) -> Tuple[List[ModelMetadata], Dict[str, str]]:
    """
    Hard-filtering step: eliminates models that cannot satisfy non-negotiable requirements.
    Returns: (eligible_models, rejected_candidates_with_reasons)
    """
    eligible: List[ModelMetadata] = []
    rejected: Dict[str, str] = {}

    for m in models:
        if not m.is_active:
            rejected[m.id] = "Model is currently disabled/inactive."
            continue

        # 1. Context Window check
        if analysis.context_size > m.context_window:
            rejected[m.id] = (
                f"Context window ({m.context_window} tokens) is smaller than required input ({analysis.context_size} tokens)."
            )
            continue

        # 2. Vision requirement check
        if analysis.vision_required and not m.supports_vision:
            rejected[m.id] = "Task requires vision / multimodal capabilities which this model does not support."
            continue

        # 3. Coding capability check (for high complexity code tasks)
        if analysis.coding_required and analysis.complexity >= 0.70 and not m.supports_coding:
            rejected[m.id] = "Task requires specialized coding capabilities for complex logic."
            continue

        # 4. Deep reasoning capability check
        if analysis.reasoning_required and analysis.complexity >= 0.85 and not m.supports_reasoning:
            rejected[m.id] = "Task requires advanced reasoning capabilities for multi-step problem solving."
            continue

        eligible.append(m)

    # If all filtered out (edge case), return active models to avoid total failure
    if not eligible and models:
        for m in models:
            if m.is_active:
                eligible.append(m)
        rejected.clear()

    return eligible, rejected


def compute_candidate_score(
    model: ModelMetadata,
    analysis: RequestAnalysis,
    weights: Dict[str, float],
) -> CandidateScore:
    """
    Multi-criteria configurable scoring formula.
    Quality, Speed, CostEfficiency, CapabilityMatch, Reliability.
    Normalized score: 0 to 100.
    """
    # 1. Quality Component (0.0 to 1.0)
    quality_comp = model.quality_score
    if analysis.quality_requirement == PriorityLevel.HIGH:
        # Boost premium models for high quality requirements
        if model.tier.value == "POWER":
            quality_comp = min(1.0, quality_comp * 1.15)
    elif analysis.quality_requirement == PriorityLevel.LOW:
        quality_comp = model.quality_score * 0.9

    # 2. Speed Component (0.0 to 1.0)
    speed_comp = model.speed_score
    if analysis.latency_priority == PriorityLevel.HIGH:
        if model.tier.value == "FAST":
            speed_comp = min(1.0, speed_comp * 1.20)
    elif analysis.latency_priority == PriorityLevel.LOW:
        speed_comp = model.speed_score * 0.85

    # 3. Cost Efficiency Component (0.0 to 1.0)
    # Zero-cost local models get 1.0, cheaper cloud models get high score
    combined_token_cost = (model.cost_per_input_token * 1000) + (model.cost_per_output_token * 1000)
    if combined_token_cost == 0.0:
        cost_efficiency = 1.0
    else:
        # Scale: $0.0001 -> 0.95, $0.01 -> 0.50, $0.05 -> 0.10
        cost_efficiency = max(0.05, min(0.99, 1.0 / (1.0 + (combined_token_cost * 100.0))))

    if analysis.cost_sensitivity == PriorityLevel.HIGH:
        cost_efficiency = min(1.0, cost_efficiency * 1.25)

    # 4. Capability Match Component (0.0 to 1.0)
    cap_points = 0.0
    total_caps = 0.0

    if analysis.coding_required:
        total_caps += 1.0
        if model.supports_coding:
            cap_points += 1.0

    if analysis.reasoning_required:
        total_caps += 1.0
        if model.supports_reasoning:
            cap_points += 1.0

    if analysis.vision_required:
        total_caps += 1.0
        if model.supports_vision:
            cap_points += 1.0

    capability_comp = (cap_points / total_caps) if total_caps > 0 else 0.90

    # 5. Reliability Component (0.0 to 1.0)
    reliability_comp = model.reliability_score

    # Weighted Sum
    w_q = weights.get("quality_weight", 0.35)
    w_c = weights.get("cost_weight", 0.25)
    w_s = weights.get("speed_weight", 0.20)
    w_cap = weights.get("capability_weight", 0.15)
    w_r = weights.get("reliability_weight", 0.05)
    total_w = w_q + w_c + w_s + w_cap + w_r

    raw_score = (
        (quality_comp * w_q)
        + (cost_efficiency * w_c)
        + (speed_comp * w_s)
        + (capability_comp * w_cap)
        + (reliability_comp * w_r)
    ) / (total_w if total_w > 0 else 1.0)

    overall_score = round(raw_score * 100.0, 2)

    # Estimated metrics
    est_latency = 120.0 if model.tier.value == "FAST" else (350.0 if model.tier.value == "BALANCED" else 750.0)
    est_cost = (analysis.context_size * model.cost_per_input_token) + (250 * model.cost_per_output_token)

    return CandidateScore(
        model_id=model.id,
        model_name=model.name,
        provider=model.provider,
        tier=model.tier.value if hasattr(model.tier, "value") else str(model.tier),
        overall_score=overall_score,
        quality_component=round(quality_comp * 100.0, 1),
        cost_component=round(cost_efficiency * 100.0, 1),
        speed_component=round(speed_comp * 100.0, 1),
        capability_component=round(capability_comp * 100.0, 1),
        reliability_component=round(reliability_comp * 100.0, 1),
        estimated_latency_ms=est_latency,
        estimated_cost_usd=round(est_cost, 6),
        eligible=True,
    )
