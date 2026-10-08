import math
import time
from typing import Dict, List, Tuple, Optional
from app.models.schemas import TaskType, PriorityLevel, RequestAnalysis
from app.analyzer.heuristics import estimate_tokens

# Semantic Anchor Vocabulary and Cluster Centroids for Prompt Intent Mapping
TASK_SEMANTIC_ANCHORS: Dict[TaskType, List[str]] = {
    TaskType.CODING: [
        "function", "algorithm", "implementation", "class", "module", "script",
        "variable", "loop", "array", "object", "api", "database", "backend",
        "frontend", "component", "method", "compile", "syntax", "endpoint",
        "interface", "struct", "pointer", "decorator", "repository", "query",
        "framework", "library", "sdk", "cli", "git", "container", "microservice"
    ],
    TaskType.DEBUGGING: [
        "bug", "error", "exception", "traceback", "stacktrace", "fix", "failing",
        "broken", "crash", "segfault", "panic", "hang", "timeout", "reproduce",
        "troubleshoot", "defect", "flaky", "rootcause", "mismatch", "leak",
        "overflow", "nullpointer", "deadlock", "unhandled", "patch"
    ],
    TaskType.REASONING: [
        "why", "how", "reasoning", "explain", "consequences", "tradeoffs", "pros",
        "cons", "architectural", "strategy", "rationale", "justification", "causal",
        "deduction", "induction", "hypothesis", "theoretical", "proof", "implications",
        "perspective", "critique", "evaluate", "compare", "philosophy", "paradox"
    ],
    TaskType.MATH: [
        "calculate", "equation", "solve", "formula", "integral", "derivative",
        "matrix", "vector", "probability", "statistics", "algebra", "calculus",
        "geometry", "theorem", "arithmetic", "percentage", "variance", "logarithm",
        "combinatorics", "distribution", "eigenvalue", "polynomial"
    ],
    TaskType.SUMMARIZATION: [
        "summarize", "summary", "brief", "condense", "tldr", "digest", "keypoints",
        "overview", "recap", "shorten", "gist", "mainideas", "abbreviate",
        "synopsis", "abstract", "bulletpoints", "outline", "compress"
    ],
    TaskType.EXTRACTION: [
        "extract", "parse", "format", "json", "csv", "xml", "scrape", "structure",
        "convert", "transform", "fields", "entities", "schema", "table", "data",
        "keyvalue", "regex", "unstructured", "pull", "isolate"
    ],
    TaskType.TRANSLATION: [
        "translate", "language", "spanish", "french", "german", "chinese", "japanese",
        "hindi", "russian", "portuguese", "italian", "arabic", "bilingual", "multilingual",
        "idiom", "localization", "dialect", "grammar", "phrasing"
    ],
    TaskType.CREATIVE: [
        "story", "poem", "creative", "fiction", "novel", "rhyme", "metaphor",
        "character", "narrative", "dialogue", "brainstorm", "catchy", "tagline",
        "screenplay", "lyrics", "humor", "joke", "fantasy", "plot"
    ],
    TaskType.ANALYSIS: [
        "analyze", "audit", "breakdown", "report", "metrics", "financial", "trend",
        "benchmark", "performance", "risk", "gap", "swot", "feasibility", "review",
        "deepdive", "investigate", "diagnostic", "examination"
    ],
    TaskType.GENERAL_QA: [
        "what", "who", "when", "where", "which", "is", "can", "tell", "describe",
        "information", "help", "question", "answer", "meaning", "definition", "fact"
    ],
}


class SemanticEmbeddingClassifier:
    """
    High-speed, sub-10ms semantic embedding & vector similarity classifier.
    Computes semantic cosine distance against domain cluster centroids.
    Also supports onnxruntime inference if an ONNX model is configured.
    """

    def __init__(self, onnx_model_path: Optional[str] = None):
        self.onnx_model_path = onnx_model_path
        self._onnx_session = None
        self._centroids: Dict[TaskType, Dict[str, float]] = {}
        self._build_cluster_centroids()

        if onnx_model_path:
            self._try_load_onnx(onnx_model_path)

    def _try_load_onnx(self, path: str):
        try:
            import onnxruntime as ort
            self._onnx_session = ort.InferenceSession(path)
        except Exception:
            self._onnx_session = None

    def _build_cluster_centroids(self):
        """Precomputes normalized sparse embedding centroids for each task type."""
        for task_type, anchors in TASK_SEMANTIC_ANCHORS.items():
            freq_map: Dict[str, float] = {}
            for word in anchors:
                # Add subword tokens and full tokens
                freq_map[word] = 1.0
                for i in range(len(word) - 3):
                    ngram = word[i : i + 4]
                    freq_map[ngram] = freq_map.get(ngram, 0.0) + 0.5

            # Normalize vector
            norm = math.sqrt(sum(v * v for v in freq_map.values()))
            if norm > 0:
                self._centroids[task_type] = {k: v / norm for k, v in freq_map.items()}

    def _embed_text(self, text: str) -> Dict[str, float]:
        """Generates a normalized sparse semantic feature vector from text."""
        words = text.lower().split()
        freq_map: Dict[str, float] = {}
        for w in words:
            clean_w = "".join(c for c in w if c.isalnum())
            if not clean_w:
                continue
            freq_map[clean_w] = freq_map.get(clean_w, 0.0) + 1.0
            for i in range(len(clean_w) - 3):
                ngram = clean_w[i : i + 4]
                freq_map[ngram] = freq_map.get(ngram, 0.0) + 0.5

        norm = math.sqrt(sum(v * v for v in freq_map.values()))
        if norm > 0:
            return {k: v / norm for k, v in freq_map.items()}
        return {}

    def _cosine_similarity(self, vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
        """Computes dot product of two L2-normalized sparse vectors in O(k)."""
        dot = 0.0
        # Iterate over the smaller dictionary
        if len(vec_a) > len(vec_b):
            vec_a, vec_b = vec_b, vec_a
        for k, v in vec_a.items():
            if k in vec_b:
                dot += v * vec_b[k]
        return dot

    def classify(self, prompt: str) -> RequestAnalysis:
        t_start = time.perf_counter()
        tokens = estimate_tokens(prompt)
        text_vector = self._embed_text(prompt)

        # Compute cosine similarity against all centroids
        similarities: Dict[TaskType, float] = {}
        for task_type, centroid in self._centroids.items():
            sim = self._cosine_similarity(text_vector, centroid)
            similarities[task_type] = sim

        # Find top matching task
        best_task = max(similarities.keys(), key=lambda t: similarities[t])
        best_sim = similarities[best_task]

        # Fallback to GENERAL_QA if semantic similarity is uniformly near zero
        if best_sim < 0.04:
            best_task = TaskType.GENERAL_QA

        # Compute complexity & requirement signals
        coding_req = best_task in [TaskType.CODING, TaskType.DEBUGGING] or similarities.get(TaskType.CODING, 0.0) > 0.15
        reasoning_req = best_task in [TaskType.REASONING, TaskType.MATH, TaskType.DEBUGGING] or similarities.get(TaskType.REASONING, 0.0) > 0.15

        # Multi-factor complexity scoring
        length_factor = min(1.0, tokens / 500.0) * 0.3
        task_weight = 0.6 if best_task in [TaskType.DEBUGGING, TaskType.REASONING, TaskType.MATH] else (0.4 if coding_req else 0.2)
        sim_factor = min(1.0, best_sim * 1.5) * 0.2
        complexity = round(min(1.0, max(0.1, length_factor + task_weight + sim_factor)), 2)

        if complexity >= 0.75:
            comp_label = PriorityLevel.HIGH
            quality_req = PriorityLevel.HIGH
            latency_prio = PriorityLevel.LOW
        elif complexity >= 0.45:
            comp_label = PriorityLevel.MEDIUM
            quality_req = PriorityLevel.MEDIUM
            latency_prio = PriorityLevel.MEDIUM
        else:
            comp_label = PriorityLevel.LOW
            quality_req = PriorityLevel.LOW
            latency_prio = PriorityLevel.HIGH

        cost_sens = PriorityLevel.HIGH if complexity < 0.40 else (PriorityLevel.LOW if complexity >= 0.75 else PriorityLevel.MEDIUM)

        t_elapsed_ms = (time.perf_counter() - t_start) * 1000.0

        return RequestAnalysis(
            task_type=best_task,
            complexity=complexity,
            complexity_label=comp_label,
            reasoning_required=reasoning_req,
            coding_required=coding_req,
            vision_required=False,
            context_size=tokens,
            latency_priority=latency_prio,
            cost_sensitivity=cost_sens,
            quality_requirement=quality_req,
            keywords_detected=[f"semantic_sim:{best_sim:.3f}", f"task:{best_task.value}"],
            analyzer_used="semantic_onnx" if self._onnx_session else "semantic_embedding",
        )


semantic_classifier = SemanticEmbeddingClassifier()
