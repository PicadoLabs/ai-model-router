from typing import List, Optional, Tuple
from app.storage.models import RoutingRuleRecord
from app.models.schemas import RequestAnalysis


def evaluate_routing_rules(
    rules: List[RoutingRuleRecord],
    analysis: RequestAnalysis,
    current_budget_percent: float = 0.0,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Evaluates enabled routing rules in order of priority (highest priority number first).
    Returns: (action_type, action_target, matched_rule_name) or (None, None, None)
    """
    sorted_rules = sorted([r for r in rules if r.is_enabled], key=lambda x: x.priority, reverse=True)

    for rule in sorted_rules:
        field = rule.condition_field.lower()
        op = rule.condition_operator
        target_val = rule.condition_value

        matched = False

        if field == "task_type":
            val = analysis.task_type.value
            if op == "==":
                matched = (val == target_val)
            elif op == "!=":
                matched = (val != target_val)
            elif op == "contains":
                matched = (target_val in val)

        elif field == "complexity":
            val = analysis.complexity
            try:
                target_num = float(target_val)
                if op == ">=":
                    matched = (val >= target_num)
                elif op == ">":
                    matched = (val > target_num)
                elif op == "<=":
                    matched = (val <= target_num)
                elif op == "<":
                    matched = (val < target_num)
                elif op == "==":
                    matched = (abs(val - target_num) < 0.01)
            except ValueError:
                pass

        elif field in ("budget_percent", "monthly_budget_percent"):
            try:
                target_num = float(target_val)
                if op == ">=":
                    matched = (current_budget_percent >= target_num)
                elif op == ">":
                    matched = (current_budget_percent > target_num)
            except ValueError:
                pass

        elif field == "context_size":
            try:
                target_num = int(target_val)
                if op == ">=":
                    matched = (analysis.context_size >= target_num)
                elif op == ">":
                    matched = (analysis.context_size > target_num)
            except ValueError:
                pass

        if matched:
            return rule.action_type, rule.action_target, rule.name

    return None, None, None
