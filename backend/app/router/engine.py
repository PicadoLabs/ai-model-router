import uuid
import datetime
from typing import List, Dict, Any, Optional
from app.models.schemas import (
    ModelMetadata,
    RequestAnalysis,
    RoutingDecision,
    CandidateScore,
    PriorityLevel,
)
from app.router.scoring import filter_candidate_models, compute_candidate_score
from app.router.rules_engine import evaluate_routing_rules
from app.storage.models import RoutingRuleRecord


def generate_routing_explanation(
    selected_model: ModelMetadata,
    analysis: RequestAnalysis,
    policy_name: str,
    rule_name: Optional[str] = None,
) -> List[str]:
    reasons = []

    if rule_name:
        reasons.append(f"Matching rule applied: \"{rule_name}\"")

    # Task explanation
    reasons.append(f"Task classified as {analysis.task_type.value} with {analysis.complexity_label.value} complexity ({analysis.complexity:.2f})")

    # Reasoning / Code requirements
    if analysis.reasoning_required:
        reasons.append("Multi-step reasoning & deep inference required for problem domain")
    if analysis.coding_required:
        reasons.append("Syntactical & algorithmic coding capabilities required")

    # Model specific match
    if selected_model.tier.value == "POWER":
        reasons.append(f"High reasoning score ({selected_model.quality_score * 100:.0f}%) and deep context ({selected_model.context_window:,} tokens)")
    elif selected_model.tier.value == "FAST":
        reasons.append(f"Low latency priority and high speed score ({selected_model.speed_score * 100:.0f}%)")
    else:
        reasons.append("Balanced quality and cost profile selected for optimal efficiency")

    # Cost / local factor
    if selected_model.cost_per_input_token == 0.0:
        reasons.append("Local zero-cost execution prioritized")
    elif analysis.cost_sensitivity == PriorityLevel.HIGH:
        reasons.append("Cost sensitivity is HIGH — model offers lowest token pricing")

    # Policy
    reasons.append(f"Evaluated under '{policy_name}' policy weights")

    return reasons


def route_request(
    analysis: RequestAnalysis,
    available_models: List[ModelMetadata],
    policy_weights: Dict[str, float],
    policy_name: str = "balanced",
    rules: Optional[List[RoutingRuleRecord]] = None,
    budget_percent: float = 0.0,
    request_id: Optional[str] = None,
) -> RoutingDecision:
    req_id = request_id or str(uuid.uuid4())
    decision_id = f"dec_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.datetime.now(datetime.UTC).isoformat()

    # 1. Rule evaluation
    rule_action, rule_target, rule_name = None, None, None
    if rules:
        rule_action, rule_target, rule_name = evaluate_routing_rules(rules, analysis, budget_percent)

    # 2. Hard filter candidates
    eligible_models, rejected_dict = filter_candidate_models(available_models, analysis)

    if not eligible_models:
        # Fallback to any active model if everything was filtered
        eligible_models = [m for m in available_models if m.is_active] or available_models

    # Handle Rule Action: ROUTE_TO specific model
    if rule_action == "ROUTE_TO" and rule_target:
        exact_match = next((m for m in eligible_models if m.id == rule_target), None)
        if exact_match:
            scores = [compute_candidate_score(m, analysis, policy_weights) for m in eligible_models]
            score_map = {s.model_id: s for s in scores}
            selected_score = score_map.get(exact_match.id) or compute_candidate_score(exact_match, analysis, policy_weights)
            
            reasons = generate_routing_explanation(exact_match, analysis, policy_name, rule_name)
            return RoutingDecision(
                decision_id=decision_id,
                request_id=req_id,
                selected_model=exact_match.id,
                selected_model_name=exact_match.name,
                provider=exact_match.provider,
                tier=exact_match.tier.value if hasattr(exact_match.tier, "value") else str(exact_match.tier),
                confidence=0.98,
                policy_used=policy_name,
                reasons=reasons,
                candidate_scores=scores,
                rejected_candidates=rejected_dict,
                estimated_cost_usd=selected_score.estimated_cost_usd,
                estimated_latency_ms=selected_score.estimated_latency_ms,
                rule_applied=rule_name,
                timestamp=now_iso,
            )

    # Handle Rule Action: FORCE_TIER
    if rule_action == "FORCE_TIER" and rule_target:
        tier_filtered = [m for m in eligible_models if m.tier.value.upper() == rule_target.upper()]
        if tier_filtered:
            eligible_models = tier_filtered

    # 3. Score all eligible models
    candidate_scores: List[CandidateScore] = []
    for model in eligible_models:
        sc = compute_candidate_score(model, analysis, policy_weights)
        candidate_scores.append(sc)

    # Sort descending by overall_score
    candidate_scores.sort(key=lambda s: s.overall_score, reverse=True)
    best_candidate = candidate_scores[0]
    selected_model = next(m for m in eligible_models if m.id == best_candidate.model_id)

    # Confidence calculation: score difference from second candidate
    if len(candidate_scores) > 1:
        gap = best_candidate.overall_score - candidate_scores[1].overall_score
        confidence = min(0.99, max(0.70, round(0.80 + (gap / 100.0), 2)))
    else:
        confidence = 0.95

    reasons = generate_routing_explanation(selected_model, analysis, policy_name, rule_name)

    return RoutingDecision(
        decision_id=decision_id,
        request_id=req_id,
        selected_model=selected_model.id,
        selected_model_name=selected_model.name,
        provider=selected_model.provider,
        tier=selected_model.tier.value if hasattr(selected_model.tier, "value") else str(selected_model.tier),
        confidence=confidence,
        policy_used=policy_name,
        reasons=reasons,
        candidate_scores=candidate_scores,
        rejected_candidates=rejected_dict,
        estimated_cost_usd=best_candidate.estimated_cost_usd,
        estimated_latency_ms=best_candidate.estimated_latency_ms,
        rule_applied=rule_name,
        timestamp=now_iso,
    )
