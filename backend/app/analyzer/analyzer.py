import json
import re
from typing import Optional
from app.models.schemas import RequestAnalysis, TaskType, PriorityLevel
from app.analyzer.heuristics import analyze_request_heuristics, estimate_tokens
from app.providers.registry import provider_registry
from app.config.settings import get_settings

settings = get_settings()

CLASSIFIER_PROMPT = """You are a real-time request classifier for an intelligent LLM model router.
Analyze the user prompt and return ONLY a JSON object matching this schema:
{
  "task_type": "GENERAL_QA" | "CODING" | "DEBUGGING" | "REASONING" | "SUMMARIZATION" | "EXTRACTION" | "WRITING" | "TRANSLATION" | "ANALYSIS" | "MATH" | "LONG_CONTEXT" | "CREATIVE",
  "complexity": 0.0 to 1.0,
  "reasoning_required": true/false,
  "coding_required": true/false,
  "vision_required": true/false,
  "latency_priority": "LOW" | "MEDIUM" | "HIGH",
  "cost_sensitivity": "LOW" | "MEDIUM" | "HIGH",
  "quality_requirement": "LOW" | "MEDIUM" | "HIGH"
}
Output valid JSON only with no markdown wrapping or additional text.
"""


async def analyze_request(prompt: str, analyzer_mode: Optional[str] = None) -> RequestAnalysis:
    mode = (analyzer_mode or settings.ROUTER_ANALYZER).lower()

    if mode == "llm":
        try:
            # Attempt to use local or configured provider for classification
            provider = provider_registry.get_provider("ollama")
            if provider:
                health = await provider.check_health()
                if health.get("status") == "CONNECTED":
                    resp = await provider.generate(
                        prompt=f"Classify this request:\n\n{prompt[:1000]}",
                        model_id="qwen2.5-coder",
                        system_prompt=CLASSIFIER_PROMPT,
                        temperature=0.1,
                    )
                    clean_json = re.search(r"\{.*\}", resp.content, re.DOTALL)
                    if clean_json:
                        data = json.loads(clean_json.group(0))
                        comp = float(data.get("complexity", 0.5))
                        comp_label = PriorityLevel.HIGH if comp >= 0.75 else (PriorityLevel.MEDIUM if comp >= 0.45 else PriorityLevel.LOW)
                        return RequestAnalysis(
                            task_type=TaskType(data.get("task_type", "GENERAL_QA")),
                            complexity=comp,
                            complexity_label=comp_label,
                            reasoning_required=bool(data.get("reasoning_required", False)),
                            coding_required=bool(data.get("coding_required", False)),
                            vision_required=bool(data.get("vision_required", False)),
                            context_size=estimate_tokens(prompt),
                            latency_priority=PriorityLevel(data.get("latency_priority", "MEDIUM")),
                            cost_sensitivity=PriorityLevel(data.get("cost_sensitivity", "MEDIUM")),
                            quality_requirement=PriorityLevel(data.get("quality_requirement", "MEDIUM")),
                            keywords_detected=["llm_classified"],
                            analyzer_used="llm",
                        )
        except Exception:
            # Graceful fallback to heuristics if LLM classifier is unavailable or times out
            pass

    # Default to fast, deterministic heuristics
    return analyze_request_heuristics(prompt)
