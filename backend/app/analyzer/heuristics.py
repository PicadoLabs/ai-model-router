import re
from typing import List, Tuple
from app.models.schemas import TaskType, PriorityLevel, RequestAnalysis

# Regex rules and indicator vocabularies
DEBUG_PATTERNS = [
    r"\b(debug|bug|stacktrace|exception|error|fix this error|traceback|segfault|syntaxerror|nullpointer)\b",
    r"\b(crash|panicked|failed test|reproduce|root cause|undefined is not a function)\b",
]

CODING_PATTERNS = [
    r"\b(write a python|write code|implement|function|class |def |const |async def|typescript|javascript|golang|rust|react|sql query|endpoint|api client)\b",
    r"\b(refactor|algorithm|regex|unit test|dockerfile|kubernetes yaml|prisma|fastapi)\b",
    r"```[a-zA-Z0-9_-]*\n",
]

REASONING_PATTERNS = [
    r"\b(explain why|reasoning|step by step|proof|derive|why did|compare and contrast|architectural decision|tradeoffs|trade-offs|consequences of)\b",
    r"\b(game theory|logical fallacy|syllogism|first principles|hypothesize)\b",
]

MATH_PATTERNS = [
    r"\b(calculate|integral|derivative|matrix|eigenvalue|probability|equation|differential equation|solve for x|combinatorics|standard deviation)\b",
    r"[\$\\\^\{\}\[\]\=]{3,}",
]

SUMMARIZATION_PATTERNS = [
    r"\b(summarize|summary|tldr|tl;dr|key points|bullet points of this|condense|digest|brief overview)\b",
]

EXTRACTION_PATTERNS = [
    r"\b(extract|extract json|parse this table|pull all emails|convert to json|output as csv|structured data from)\b",
]

TRANSLATION_PATTERNS = [
    r"\b(translate to|translate into|in french|in spanish|in german|in japanese|in chinese|in hindi|translate from)\b",
]

CREATIVE_PATTERNS = [
    r"\b(write a poem|write a story|screenplay|brainstorm catchy|creative writing|dialogue between|fiction|metaphor)\b",
]

ANALYSIS_PATTERNS = [
    r"\b(analyze|breakdown|evaluate|critique|audit|financial report|trend analysis|pros and cons)\b",
]


def estimate_tokens(text: str) -> int:
    """Fast, reliable token estimation (roughly 4 characters per token)."""
    return max(1, len(text) // 4)


def analyze_request_heuristics(prompt: str) -> RequestAnalysis:
    text_lower = prompt.lower()
    tokens = estimate_tokens(prompt)
    
    detected_keywords: List[str] = []
    task_scores: dict[TaskType, float] = {t: 0.0 for t in TaskType}
    
    # 1. Evaluate patterns
    for p in DEBUG_PATTERNS:
        matches = re.findall(p, text_lower)
        if matches:
            task_scores[TaskType.DEBUGGING] += len(matches) * 2.5
            detected_keywords.extend(matches)

    for p in CODING_PATTERNS:
        matches = re.findall(p, text_lower)
        if matches:
            task_scores[TaskType.CODING] += len(matches) * 2.0
            detected_keywords.extend(matches)

    for p in REASONING_PATTERNS:
        matches = re.findall(p, text_lower)
        if matches:
            task_scores[TaskType.REASONING] += len(matches) * 2.0
            detected_keywords.extend(matches)

    for p in MATH_PATTERNS:
        matches = re.findall(p, text_lower)
        if matches:
            task_scores[TaskType.MATH] += len(matches) * 2.2
            detected_keywords.extend(matches)

    for p in SUMMARIZATION_PATTERNS:
        matches = re.findall(p, text_lower)
        if matches:
            task_scores[TaskType.SUMMARIZATION] += len(matches) * 2.5
            detected_keywords.extend(matches)

    for p in EXTRACTION_PATTERNS:
        matches = re.findall(p, text_lower)
        if matches:
            task_scores[TaskType.EXTRACTION] += len(matches) * 2.0
            detected_keywords.extend(matches)

    for p in TRANSLATION_PATTERNS:
        matches = re.findall(p, text_lower)
        if matches:
            task_scores[TaskType.TRANSLATION] += len(matches) * 3.0
            detected_keywords.extend(matches)

    for p in CREATIVE_PATTERNS:
        matches = re.findall(p, text_lower)
        if matches:
            task_scores[TaskType.CREATIVE] += len(matches) * 2.0
            detected_keywords.extend(matches)

    for p in ANALYSIS_PATTERNS:
        matches = re.findall(p, text_lower)
        if matches:
            task_scores[TaskType.ANALYSIS] += len(matches) * 1.8
            detected_keywords.extend(matches)

    # Long context check
    if tokens > 4000:
        task_scores[TaskType.LONG_CONTEXT] += 3.0

    # 2. Determine Primary Task
    best_task = TaskType.GENERAL_QA
    max_score = 0.0
    for task, score in task_scores.items():
        if score > max_score:
            max_score = score
            best_task = task

    # 3. Derive Complexity (0.0 to 1.0)
    complexity = 0.35  # Base complexity
    
    # Token length factor
    if tokens > 10000:
        complexity += 0.30
    elif tokens > 3000:
        complexity += 0.20
    elif tokens > 800:
        complexity += 0.10
    elif tokens < 30:
        complexity -= 0.10

    # Task inherent complexity
    if best_task in (TaskType.DEBUGGING, TaskType.MATH, TaskType.REASONING):
        complexity += 0.30
    elif best_task in (TaskType.CODING, TaskType.ANALYSIS, TaskType.LONG_CONTEXT):
        complexity += 0.20
    elif best_task in (TaskType.TRANSLATION, TaskType.EXTRACTION, TaskType.SUMMARIZATION):
        complexity += 0.05
    elif best_task == TaskType.GENERAL_QA and tokens < 50:
        complexity -= 0.15

    # Multi-step keyword boosts
    if any(k in text_lower for k in ["distributed", "async", "concurrency", "deadlock", "microservices", "architecture"]):
        complexity += 0.25
    if any(k in text_lower for k in ["simple", "quick", "one liner", "easy", "hello world"]):
        complexity -= 0.20

    complexity = max(0.05, min(0.99, round(complexity, 2)))

    # 4. Priority and Capabilities
    coding_required = best_task in (TaskType.CODING, TaskType.DEBUGGING) or task_scores[TaskType.CODING] > 0
    reasoning_required = best_task in (TaskType.REASONING, TaskType.DEBUGGING, TaskType.MATH) or complexity >= 0.70

    if complexity >= 0.75:
        complexity_label = PriorityLevel.HIGH
        quality_req = PriorityLevel.HIGH
        latency_pri = PriorityLevel.LOW
        cost_sens = PriorityLevel.LOW
    elif complexity >= 0.45:
        complexity_label = PriorityLevel.MEDIUM
        quality_req = PriorityLevel.MEDIUM
        latency_pri = PriorityLevel.MEDIUM
        cost_sens = PriorityLevel.MEDIUM
    else:
        complexity_label = PriorityLevel.LOW
        quality_req = PriorityLevel.LOW
        latency_pri = PriorityLevel.HIGH
        cost_sens = PriorityLevel.HIGH

    return RequestAnalysis(
        task_type=best_task,
        complexity=complexity,
        complexity_label=complexity_label,
        reasoning_required=reasoning_required,
        coding_required=coding_required,
        vision_required=False,
        tools_required=False,
        context_size=tokens,
        latency_priority=latency_pri,
        cost_sensitivity=cost_sens,
        quality_requirement=quality_req,
        keywords_detected=list(set(detected_keywords))[:10],
        analyzer_used="rules",
    )
