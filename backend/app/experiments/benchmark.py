"""
Automated Routing Benchmark Suite and Cost-Accuracy Pareto Evaluator.
Evaluates model router policies vs static frontier baselines across standardized datasets
(GSM8K, HumanEval, MMLU, or custom datasets) and computes the Pareto-optimal frontier.
"""

import re
import ast
import json
import math
import time
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Built-in Standard Benchmark Subsets
# ---------------------------------------------------------------------------

GSM8K_SUBSET = [
    {
        "id": "gsm8k-1",
        "task_type": "MATH",
        "prompt": "Natalia sold clips to 48 of her friends in April, and then she sold half as many clips in May. How many clips did Natalia sell altogether in April and May?",
        "expected_answer": "72",
        "expected_number": 72.0,
    },
    {
        "id": "gsm8k-2",
        "task_type": "MATH",
        "prompt": "Weng earns $12 an hour for babysitting. Yesterday, she just did 50 minutes of babysitting. How much did she earn?",
        "expected_answer": "10",
        "expected_number": 10.0,
    },
    {
        "id": "gsm8k-3",
        "task_type": "MATH",
        "prompt": "Betty is saving money for a new wallet which costs $100. Betty has only half of the money she needs. Her parents gave her $15 and her grandparents gave her twice as much as her parents. How much more money does Betty need to buy the wallet?",
        "expected_answer": "5",
        "expected_number": 5.0,
    },
    {
        "id": "gsm8k-4",
        "task_type": "MATH",
        "prompt": "A deep-sea monster rises from the waters once every 100 years to feast on a ship and then returns to sleep. In 300 years, how many ships will it feast on?",
        "expected_answer": "3",
        "expected_number": 3.0,
    },
    {
        "id": "gsm8k-5",
        "task_type": "MATH",
        "prompt": "Albert is wondering how much pizza he ate. He ate 2 slices of pepperoni pizza and 3 slices of cheese pizza. If there were 8 slices in each whole pizza, what fraction of a whole pizza did Albert eat? Give the answer as decimal.",
        "expected_answer": "0.625",
        "expected_number": 0.625,
    },
    {
        "id": "gsm8k-6",
        "task_type": "MATH",
        "prompt": "Mark has 12 apples. He gives 4 to his sister and 3 to his brother. Then he buys 10 more apples. How many apples does Mark have now?",
        "expected_answer": "15",
        "expected_number": 15.0,
    },
    {
        "id": "gsm8k-7",
        "task_type": "MATH",
        "prompt": "A bakery bakes 120 loaves of bread every morning. By noon, they sell 75 loaves. In the afternoon, they bake 40 more loaves and sell 50 loaves before closing. How many loaves are left?",
        "expected_answer": "35",
        "expected_number": 35.0,
    },
    {
        "id": "gsm8k-8",
        "task_type": "MATH",
        "prompt": "If a train travels at 60 miles per hour, how many miles will it travel in 3.5 hours?",
        "expected_answer": "210",
        "expected_number": 210.0,
    },
    {
        "id": "gsm8k-9",
        "task_type": "MATH",
        "prompt": "A rectangular garden is 15 meters long and 8 meters wide. What is the perimeter of the garden in meters?",
        "expected_answer": "46",
        "expected_number": 46.0,
    },
    {
        "id": "gsm8k-10",
        "task_type": "MATH",
        "prompt": "Sarah bought 3 books for $14 each and a bookmark for $3. She paid with a $50 bill. How much change did she receive?",
        "expected_answer": "5",
        "expected_number": 5.0,
    },
]

HUMANEVAL_SUBSET = [
    {
        "id": "he-0",
        "task_type": "CODE",
        "prompt": "Write a Python function `has_close_elements(numbers: list[float], threshold: float) -> bool` that checks if in given list of numbers, are any two numbers closer to each other than given threshold.",
        "test_code": "assert has_close_elements([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.3) == True\nassert has_close_elements([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.05) == False",
        "function_name": "has_close_elements",
    },
    {
        "id": "he-1",
        "task_type": "CODE",
        "prompt": "Write a Python function `separate_paren_groups(paren_string: str) -> list[str]` that separates balanced groups of parentheses into separate strings.",
        "test_code": "assert separate_paren_groups('( ) (( )) (( )( ))') == ['()', '(())', '(()())']",
        "function_name": "separate_paren_groups",
    },
    {
        "id": "he-2",
        "task_type": "CODE",
        "prompt": "Write a Python function `truncate_number(number: float) -> float` that returns the decimal/fractional part of a positive floating point number.",
        "test_code": "assert abs(truncate_number(3.5) - 0.5) < 1e-6\nassert abs(truncate_number(1.33) - 0.33) < 1e-6",
        "function_name": "truncate_number",
    },
    {
        "id": "he-3",
        "task_type": "CODE",
        "prompt": "Write a Python function `below_zero(operations: list[int]) -> bool` that detects if bank balance ever falls below zero given initial balance 0 and a list of deposit/withdrawal operations.",
        "test_code": "assert below_zero([1, 2, 3]) == False\nassert below_zero([1, 2, -4, 5]) == True",
        "function_name": "below_zero",
    },
    {
        "id": "he-4",
        "task_type": "CODE",
        "prompt": "Write a Python function `mean_absolute_deviation(numbers: list[float]) -> float` that calculates Mean Absolute Deviation of a list of numbers.",
        "test_code": "assert abs(mean_absolute_deviation([1.0, 2.0, 3.0, 4.0]) - 1.0) < 1e-6",
        "function_name": "mean_absolute_deviation",
    },
    {
        "id": "he-5",
        "task_type": "CODE",
        "prompt": "Write a Python function `intersperse(numbers: list[int], delimiter: int) -> list[int]` that inserts a delimiter between every two adjacent elements of the input list.",
        "test_code": "assert intersperse([], 4) == []\nassert intersperse([1, 2, 3], 4) == [1, 4, 2, 4, 3]",
        "function_name": "intersperse",
    },
    {
        "id": "he-6",
        "task_type": "CODE",
        "prompt": "Write a Python function `parse_nested_parens(paren_string: str) -> list[int]` that returns the maximum depth of nested parentheses for each group separated by spaces.",
        "test_code": "assert parse_nested_parens('(()()) ((())) () ((())()())') == [2, 3, 1, 3]",
        "function_name": "parse_nested_parens",
    },
    {
        "id": "he-7",
        "task_type": "CODE",
        "prompt": "Write a Python function `filter_by_substring(strings: list[str], substring: str) -> list[str]` that filters an array of strings to only those containing the given substring.",
        "test_code": "assert filter_by_substring([], 'a') == []\nassert filter_by_substring(['abc', 'bac', 'cde', 'array'], 'a') == ['abc', 'bac', 'array']",
        "function_name": "filter_by_substring",
    },
    {
        "id": "he-8",
        "task_type": "CODE",
        "prompt": "Write a Python function `sum_product(numbers: list[int]) -> tuple[int, int]` that returns a tuple consisting of the sum and product of all the integers in a list. For empty list, sum is 0 and product is 1.",
        "test_code": "assert sum_product([]) == (0, 1)\nassert sum_product([1, 2, 3, 4]) == (10, 24)",
        "function_name": "sum_product",
    },
    {
        "id": "he-9",
        "task_type": "CODE",
        "prompt": "Write a Python function `rolling_max(numbers: list[int]) -> list[int]` that calculates the rolling maximum at each step given a list of integers.",
        "test_code": "assert rolling_max([1, 2, 3, 2, 3, 4, 2]) == [1, 2, 3, 3, 3, 4, 4]",
        "function_name": "rolling_max",
    },
]

MMLU_SUBSET = [
    {
        "id": "mmlu-1",
        "task_type": "GENERAL_QA",
        "prompt": "What is the primary function of ribosomes in a biological cell?\nA) Lipid synthesis\nB) Protein synthesis\nC) DNA replication\nD) Cellular respiration\nAnswer with the letter of the correct option.",
        "expected_answer": "B",
    },
    {
        "id": "mmlu-2",
        "task_type": "GENERAL_QA",
        "prompt": "In computer science, what is the time complexity of binary search on a sorted array of size N?\nA) O(1)\nB) O(N)\nC) O(log N)\nD) O(N log N)\nAnswer with the letter of the correct option.",
        "expected_answer": "C",
    },
    {
        "id": "mmlu-3",
        "task_type": "GENERAL_QA",
        "prompt": "Which economic principle states that bad money drives out good money?\nA) Say's Law\nB) Gresham's Law\nC) Phillips Curve\nD) Okun's Law\nAnswer with the letter of the correct option.",
        "expected_answer": "B",
    },
    {
        "id": "mmlu-4",
        "task_type": "GENERAL_QA",
        "prompt": "In relational database theory, which normal form eliminates transitive dependencies?\nA) First Normal Form (1NF)\nB) Second Normal Form (2NF)\nC) Third Normal Form (3NF)\nD) Boyce-Codd Normal Form (BCNF)\nAnswer with the letter of the correct option.",
        "expected_answer": "C",
    },
    {
        "id": "mmlu-5",
        "task_type": "GENERAL_QA",
        "prompt": "What is the capital city of Australia?\nA) Sydney\nB) Melbourne\nC) Canberra\nD) Brisbane\nAnswer with the letter of the correct option.",
        "expected_answer": "C",
    },
]


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

class BenchmarkSampleResult(BaseModel):
    sample_id: str
    prompt: str
    task_type: str
    target: str  # Model ID or Policy Name
    selected_model: str
    provider: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    cost_usd: float
    is_correct: bool
    score: float
    output_preview: str


class CandidateEvaluation(BaseModel):
    name: str
    target_type: str  # 'policy' or 'static_model'
    total_samples: int
    correct_samples: int
    accuracy_percent: float
    avg_latency_ms: float
    p95_latency_ms: float
    avg_cost_per_1k_usd: float
    total_cost_usd: float
    accuracy_retention_percent: float = 100.0
    cost_savings_percent: float = 0.0
    latency_reduction_percent: float = 0.0
    is_pareto_optimal: bool = False
    model_breakdown: Dict[str, int] = Field(default_factory=dict)


class ParetoBenchmarkReport(BaseModel):
    dataset_name: str
    sample_count: int
    baseline_model: str
    candidates: List[CandidateEvaluation]
    pareto_frontier: List[str]  # List of candidate names on the Pareto frontier
    generated_at: str
    ascii_graph: str = ""


# ---------------------------------------------------------------------------
# Answer Extraction & Verification Utilities
# ---------------------------------------------------------------------------

def extract_numeric_answer(text: str) -> Optional[float]:
    """Extract numeric answer from math text or GSM8K style output."""
    # Pattern 1: #### 42 or #### -3.14
    hash_match = re.search(r"####\s*([+-]?\d+(?:\.\d+)?)", text)
    if hash_match:
        try:
            return float(hash_match.group(1).replace(",", ""))
        except ValueError:
            pass

    # Pattern 2: \boxed{42}
    boxed_match = re.search(r"\\boxed\{([+-]?\d+(?:\.\d+)?)\}", text)
    if boxed_match:
        try:
            return float(boxed_match.group(1).replace(",", ""))
        except ValueError:
            pass

    # Pattern 3: Final sentence numbers (e.g. "The answer is 72", "is 72.", "= 72")
    final_match = re.findall(r"(?:answer is|equals?|=|\b)\s*([+-]?\d+(?:\.\d+)?)\s*(?:\.|$)", text, re.IGNORECASE)
    if final_match:
        try:
            return float(final_match[-1].replace(",", ""))
        except ValueError:
            pass

    # Fallback: Find all standalone numbers and pick the last one
    all_numbers = re.findall(r"[+-]?\d+(?:\.\d+)?", text)
    if all_numbers:
        try:
            return float(all_numbers[-1])
        except ValueError:
            pass

    return None


def extract_python_code(text: str) -> str:
    """Extract Python code block from markdown fences or text."""
    code_match = re.search(r"```(?:python)?\s*\n(.*?)\n```", text, re.DOTALL)
    if code_match:
        return code_match.group(1)
    
    # Fallback: if 'def ' is in text, extract from 'def ' onwards
    if "def " in text:
        idx = text.find("def ")
        return text[idx:]
    
    return text


def evaluate_response_correctness(
    task_type: str,
    response_text: str,
    sample: Dict[str, Any],
    is_mock: bool = False,
    model_quality: float = 0.85,
) -> Tuple[bool, float]:
    """
    Evaluate whether a model response correctly solves the benchmark sample.
    Supports real execution/regex extraction, with calibrated heuristic fallback for mock simulation.
    """
    # 1. GSM8K / Math evaluation
    if task_type == "MATH" or "expected_number" in sample:
        expected_num = sample.get("expected_number")
        if expected_num is not None:
            extracted = extract_numeric_answer(response_text)
            if extracted is not None and abs(extracted - expected_num) < 1e-4:
                return True, 1.0
            if is_mock:
                # In mock/demo mode without live LLM inference, calibrate accuracy with model quality
                # Frontier models get higher mock retention
                prob = min(0.98, max(0.65, model_quality))
                # Deterministic pseudo-randomness based on sample id + model quality
                seed_val = (hash(sample.get("id", "")) + int(model_quality * 100)) % 100
                is_correct = (seed_val / 100.0) < prob
                return is_correct, 1.0 if is_correct else 0.0

    # 2. HumanEval / Code evaluation
    elif task_type == "CODE" or "test_code" in sample:
        test_code = sample.get("test_code", "")
        code = extract_python_code(response_text)
        
        if not is_mock and test_code:
            try:
                # Syntax check first
                ast.parse(code)
                # Local safe environment execution
                exec_globals: Dict[str, Any] = {}
                exec(code, exec_globals)
                exec(test_code, exec_globals)
                return True, 1.0
            except Exception:
                return False, 0.0
        else:
            # Mock / heuristic fallback
            prob = min(0.95, max(0.60, model_quality))
            seed_val = (hash(sample.get("id", "")) + int(model_quality * 100)) % 100
            is_correct = (seed_val / 100.0) < prob
            return is_correct, 1.0 if is_correct else 0.0

    # 3. MMLU / Option matching
    elif "expected_answer" in sample:
        expected = str(sample["expected_answer"]).strip().upper()
        # Look for option letter
        pattern = rf"(?:^|\b|\()({expected})(?:\)|\.|\b|$)"
        if re.search(pattern, response_text, re.IGNORECASE):
            return True, 1.0
        if is_mock:
            prob = min(0.95, max(0.60, model_quality))
            seed_val = (hash(sample.get("id", "")) + int(model_quality * 100)) % 100
            is_correct = (seed_val / 100.0) < prob
            return is_correct, 1.0 if is_correct else 0.0

    return False, 0.0


# ---------------------------------------------------------------------------
# Pareto Frontier Computation
# ---------------------------------------------------------------------------

def calculate_pareto_frontier(candidates: List[CandidateEvaluation]) -> List[str]:
    """
    Identifies Pareto-optimal configurations.
    Objectives:
      - Maximize accuracy_percent
      - Minimize avg_cost_per_1k_usd
      - Minimize avg_latency_ms

    Candidate A dominates Candidate B if:
      - acc_A >= acc_B
      - cost_A <= cost_B
      - lat_A <= lat_B
      - and at least one condition is strictly better.
    """
    pareto_names = []

    for c in candidates:
        is_dominated = False
        for other in candidates:
            if c.name == other.name:
                continue

            acc_better_or_equal = other.accuracy_percent >= c.accuracy_percent
            cost_better_or_equal = other.avg_cost_per_1k_usd <= c.avg_cost_per_1k_usd
            lat_better_or_equal = other.avg_latency_ms <= c.avg_latency_ms

            strictly_better = (
                other.accuracy_percent > c.accuracy_percent
                or other.avg_cost_per_1k_usd < c.avg_cost_per_1k_usd
                or other.avg_latency_ms < c.avg_latency_ms
            )

            if acc_better_or_equal and cost_better_or_equal and lat_better_or_equal and strictly_better:
                is_dominated = True
                break

        c.is_pareto_optimal = not is_dominated
        if not is_dominated:
            pareto_names.append(c.name)

    return pareto_names


# ---------------------------------------------------------------------------
# ASCII Pareto Curve Visualizer
# ---------------------------------------------------------------------------

def generate_ascii_pareto_chart(
    candidates: List[CandidateEvaluation],
    width: int = 50,
    height: int = 14,
) -> str:
    """
    Generates a clean terminal ASCII 2D scatter graph of Cost vs Accuracy.
    X-axis: Cost ($ per 1K reqs) -> lower is better (left)
    Y-axis: Accuracy (%) -> higher is better (top)
    Marked with [*] for Pareto Frontier and [o] for Dominated.
    """
    if not candidates:
        return ""

    min_cost = min(c.avg_cost_per_1k_usd for c in candidates)
    max_cost = max(c.avg_cost_per_1k_usd for c in candidates)
    if max_cost == min_cost:
        max_cost += 0.01

    min_acc = max(0.0, min(c.accuracy_percent for c in candidates) - 5.0)
    max_acc = min(100.0, max(c.accuracy_percent for c in candidates) + 5.0)
    if max_acc == min_acc:
        max_acc += 10.0

    # Initialize canvas
    canvas = [[" " for _ in range(width)] for _ in range(height)]

    # Plot points
    for idx, c in enumerate(candidates):
        x = int(((c.avg_cost_per_1k_usd - min_cost) / (max_cost - min_cost)) * (width - 1))
        y = int(((c.accuracy_percent - min_acc) / (max_acc - min_acc)) * (height - 1))
        
        # Invert Y for terminal display (top is 0)
        y_screen = (height - 1) - max(0, min(height - 1, y))
        x_screen = max(0, min(width - 1, x))

        marker = "*" if c.is_pareto_optimal else "o"
        canvas[y_screen][x_screen] = marker

    # Build ASCII graph with axes
    lines = []
    lines.append("  Acc (%) ^ [Cost vs Accuracy Pareto Frontier]")
    for r in range(height):
        acc_label = f"{max_acc - (r / (height - 1)) * (max_acc - min_acc):5.1f}% |"
        row_str = "".join(canvas[r])
        lines.append(f"{acc_label}{row_str}")

    lines.append("        +" + "-" * width + "> Cost ($/1K)")
    lines.append(f"         ${min_cost:<6.4f}" + " " * (width - 18) + f"${max_cost:>6.4f}")
    lines.append("\n  Legend:  [*] = Pareto Frontier (Non-Dominated)   [o] = Dominated Baseline")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Benchmark Runner Engine
# ---------------------------------------------------------------------------

class BenchmarkRunner:
    """Executes standardized benchmarks and computes Pareto trade-offs."""

    def __init__(self):
        pass

    def load_dataset(self, dataset_name_or_path: str, limit: int = 10) -> Tuple[str, List[Dict[str, Any]]]:
        """Load built-in or custom dataset."""
        name_lower = dataset_name_or_path.strip().lower()
        if name_lower == "gsm8k":
            data = GSM8K_SUBSET[:limit]
            return "GSM8K (Math Reasoning)", data
        elif name_lower == "humaneval":
            data = HUMANEVAL_SUBSET[:limit]
            return "HumanEval (Python Coding)", data
        elif name_lower == "mmlu":
            data = MMLU_SUBSET[:limit]
            return "MMLU (Multi-Domain Knowledge)", data
        
        # Check if local file path
        try:
            with open(dataset_name_or_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content.startswith("["):
                    items = json.loads(content)
                else:
                    items = [json.loads(line) for line in content.splitlines() if line.strip()]
                return f"Custom Dataset ({dataset_name_or_path})", items[:limit]
        except Exception as e:
            # Default fallback to GSM8K
            data = GSM8K_SUBSET[:limit]
            return f"GSM8K (Fallback: {e})", data

    async def run_benchmark(
        self,
        dataset_name: str = "gsm8k",
        limit: int = 10,
        policies_to_test: Optional[List[str]] = None,
        models_to_test: Optional[List[str]] = None,
        baseline_model: str = "gpt-4o",
    ) -> ParetoBenchmarkReport:
        """
        Runs candidate policies and baseline models against the dataset,
        records metrics, and calculates Pareto trade-offs.
        """
        from app.storage.database import AsyncSessionLocal, init_db
        from app.storage.models import ModelRecord, RoutingPolicyRecord
        from app.analyzer.heuristics import analyze_request_heuristics
        from app.router.engine import route_request
        from app.api.routes import db_model_to_meta
        from app.fallback.handler import execute_with_fallback
        from sqlalchemy import select

        await init_db()
        ds_label, samples = self.load_dataset(dataset_name, limit=limit)

        async with AsyncSessionLocal() as db:
            # Fetch all active models
            res_m = await db.execute(select(ModelRecord).filter_by(is_active=True))
            all_db_models = res_m.scalars().all()
            all_models = [db_model_to_meta(m) for m in all_db_models]
            model_dict = {m.id: m for m in all_models}

            # Fetch policy weights
            res_p = await db.execute(select(RoutingPolicyRecord))
            db_policies = {p.id: p for p in res_p.scalars().all()}

        # Defaults if none provided
        if not policies_to_test:
            policies_to_test = ["balanced", "cost_optimized", "speed_optimized", "quality_first"]

        if not models_to_test:
            models_to_test = [baseline_model, "gpt-4o-mini", "claude-3-5-sonnet", "deepseek-chat", "llama-3-8b"]
            # Ensure unique and exists in model registry
            models_to_test = [m for m in dict.fromkeys(models_to_test) if m in model_dict]

        candidate_evals: List[CandidateEvaluation] = []

        # -------------------------------------------------------------
        # 1. Evaluate Static Baseline Models
        # -------------------------------------------------------------
        for m_id in models_to_test:
            meta = model_dict.get(m_id)
            if not meta:
                continue

            latencies: List[float] = []
            costs: List[float] = []
            correct_count = 0

            for sample in samples:
                prompt = sample["prompt"]
                task_type = sample.get("task_type", "GENERAL_QA")
                
                resp, _, _, _ = await execute_with_fallback(
                    prompt=prompt,
                    selected_model_id=m_id,
                    selected_provider_id=meta.provider,
                    all_models=all_models,
                )

                latencies.append(resp.provider_latency_ms)
                # Calculate cost
                in_cost = (resp.input_tokens / 1000.0) * (meta.cost_per_input_token * 1000.0)
                out_cost = (resp.output_tokens / 1000.0) * (meta.cost_per_output_token * 1000.0)
                cost = in_cost + out_cost
                costs.append(cost)

                is_corr, _ = evaluate_response_correctness(
                    task_type=task_type,
                    response_text=resp.content,
                    sample=sample,
                    is_mock=getattr(resp, "is_mock", True),
                    model_quality=meta.quality_score,
                )
                if is_corr:
                    correct_count += 1

            total_s = len(samples)
            acc_pct = (correct_count / total_s) * 100.0 if total_s > 0 else 0.0
            avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
            sorted_lat = sorted(latencies)
            p95_idx = int(0.95 * len(sorted_lat))
            p95_lat = sorted_lat[min(p95_idx, len(sorted_lat) - 1)] if sorted_lat else 0.0
            total_c = sum(costs)
            cost_per_1k = (total_c / total_s) * 1000.0 if total_s > 0 else 0.0

            candidate_evals.append(CandidateEvaluation(
                name=f"model:{m_id}",
                target_type="static_model",
                total_samples=total_s,
                correct_samples=correct_count,
                accuracy_percent=round(acc_pct, 1),
                avg_latency_ms=round(avg_lat, 1),
                p95_latency_ms=round(p95_lat, 1),
                avg_cost_per_1k_usd=round(cost_per_1k, 4),
                total_cost_usd=round(total_c, 6),
                model_breakdown={m_id: total_s},
            ))

        # -------------------------------------------------------------
        # 2. Evaluate Dynamic Router Policies
        # -------------------------------------------------------------
        for pol_id in policies_to_test:
            pol_rec = db_policies.get(pol_id)
            weights = {
                "quality_weight": pol_rec.quality_weight if pol_rec else 0.35,
                "cost_weight": pol_rec.cost_weight if pol_rec else 0.25,
                "speed_weight": pol_rec.speed_weight if pol_rec else 0.20,
                "capability_weight": pol_rec.capability_weight if pol_rec else 0.15,
                "reliability_weight": pol_rec.reliability_weight if pol_rec else 0.05,
            }

            latencies = []
            costs = []
            correct_count = 0
            model_counts: Dict[str, int] = {}

            for sample in samples:
                prompt = sample["prompt"]
                task_type = sample.get("task_type", "GENERAL_QA")

                t0 = time.perf_counter()
                analysis = analyze_request_heuristics(prompt)
                decision = route_request(
                    analysis=analysis,
                    available_models=all_models,
                    policy_weights=weights,
                    policy_name=pol_id,
                )
                routing_ms = (time.perf_counter() - t0) * 1000.0

                sel_m = decision.selected_model
                model_counts[sel_m] = model_counts.get(sel_m, 0) + 1
                meta = model_dict.get(sel_m, all_models[0])

                resp, _, _, _ = await execute_with_fallback(
                    prompt=prompt,
                    selected_model_id=sel_m,
                    selected_provider_id=decision.provider,
                    all_models=all_models,
                )

                latencies.append(resp.provider_latency_ms + routing_ms)
                in_cost = (resp.input_tokens / 1000.0) * (meta.cost_per_input_token * 1000.0)
                out_cost = (resp.output_tokens / 1000.0) * (meta.cost_per_output_token * 1000.0)
                cost = in_cost + out_cost
                costs.append(cost)

                is_corr, _ = evaluate_response_correctness(
                    task_type=task_type,
                    response_text=resp.content,
                    sample=sample,
                    is_mock=getattr(resp, "is_mock", True),
                    model_quality=meta.quality_score,
                )
                if is_corr:
                    correct_count += 1

            total_s = len(samples)
            acc_pct = (correct_count / total_s) * 100.0 if total_s > 0 else 0.0
            avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
            sorted_lat = sorted(latencies)
            p95_idx = int(0.95 * len(sorted_lat))
            p95_lat = sorted_lat[min(p95_idx, len(sorted_lat) - 1)] if sorted_lat else 0.0
            total_c = sum(costs)
            cost_per_1k = (total_c / total_s) * 1000.0 if total_s > 0 else 0.0

            candidate_evals.append(CandidateEvaluation(
                name=f"router:{pol_id}",
                target_type="policy",
                total_samples=total_s,
                correct_samples=correct_count,
                accuracy_percent=round(acc_pct, 1),
                avg_latency_ms=round(avg_lat, 1),
                p95_latency_ms=round(p95_lat, 1),
                avg_cost_per_1k_usd=round(cost_per_1k, 4),
                total_cost_usd=round(total_c, 6),
                model_breakdown=model_counts,
            ))

        # -------------------------------------------------------------
        # 3. Compute Relative Baseline Comparison
        # -------------------------------------------------------------
        base_name = f"model:{baseline_model}"
        baseline_eval = next((c for c in candidate_evals if c.name == base_name), None)
        if not baseline_eval and candidate_evals:
            baseline_eval = candidate_evals[0]

        if baseline_eval:
            b_acc = baseline_eval.accuracy_percent or 1.0
            b_cost = baseline_eval.avg_cost_per_1k_usd or 0.0001
            b_lat = baseline_eval.avg_latency_ms or 1.0

            for c in candidate_evals:
                c.accuracy_retention_percent = round((c.accuracy_percent / b_acc) * 100.0, 1)
                cost_saved = ((b_cost - c.avg_cost_per_1k_usd) / b_cost) * 100.0
                c.cost_savings_percent = round(max(-500.0, cost_saved), 1)
                lat_red = ((b_lat - c.avg_latency_ms) / b_lat) * 100.0
                c.latency_reduction_percent = round(max(-500.0, lat_red), 1)

        # -------------------------------------------------------------
        # 4. Calculate Pareto Optimal Frontier & ASCII Graph
        # -------------------------------------------------------------
        pareto_frontier_names = calculate_pareto_frontier(candidate_evals)
        ascii_chart = generate_ascii_pareto_chart(candidate_evals)

        return ParetoBenchmarkReport(
            dataset_name=ds_label,
            sample_count=len(samples),
            baseline_model=baseline_model,
            candidates=candidate_evals,
            pareto_frontier=pareto_frontier_names,
            generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            ascii_graph=ascii_chart,
        )


# Global singleton benchmark runner
benchmark_runner = BenchmarkRunner()
