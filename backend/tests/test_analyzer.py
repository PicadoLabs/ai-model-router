import pytest
from app.analyzer.heuristics import analyze_request_heuristics, estimate_tokens
from app.models.schemas import TaskType, PriorityLevel


def test_token_estimation():
    text = "Hello world from Model Router platform!"
    tokens = estimate_tokens(text)
    assert tokens > 0


def test_heuristic_classification_coding():
    prompt = "Write a python function to calculate fibonacci sequence using dynamic programming"
    analysis = analyze_request_heuristics(prompt)
    assert analysis.task_type == TaskType.CODING
    assert analysis.coding_required is True
    assert analysis.complexity >= 0.40


def test_heuristic_classification_debugging_complexity():
    prompt = "Debug this distributed async deadlock issue in the microservices cluster and explain the root cause"
    analysis = analyze_request_heuristics(prompt)
    assert analysis.task_type == TaskType.DEBUGGING
    assert analysis.reasoning_required is True
    assert analysis.coding_required is True
    assert analysis.complexity_label == PriorityLevel.HIGH
    assert analysis.complexity >= 0.75


def test_heuristic_classification_summarization():
    prompt = "Provide a summary and key bullet points of this meeting transcript"
    analysis = analyze_request_heuristics(prompt)
    assert analysis.task_type == TaskType.SUMMARIZATION
    assert analysis.complexity_label in (PriorityLevel.LOW, PriorityLevel.MEDIUM)


def test_heuristic_classification_math():
    prompt = "Calculate the derivative and integral of matrix eigenvalue differential equation"
    analysis = analyze_request_heuristics(prompt)
    assert analysis.task_type == TaskType.MATH
    assert analysis.reasoning_required is True
