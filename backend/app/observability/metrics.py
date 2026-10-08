import time
from typing import Dict, Optional, Tuple
from app.config.settings import get_settings

settings = get_settings()

try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        generate_latest,
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        REGISTRY,
    )
    PROMETHEUS_CLIENT_AVAILABLE = True
except ImportError:
    PROMETHEUS_CLIENT_AVAILABLE = False


class MetricsCollector:
    """
    Standard Prometheus metrics collector for AI Model Router.
    Tracks request volumes, routing latency, provider latency, token throughput,
    and cost savings.
    """

    def __init__(self):
        if PROMETHEUS_CLIENT_AVAILABLE:
            self.registry = REGISTRY
            self.requests_total = Counter(
                "model_router_requests_total",
                "Total number of routed requests",
                ["task_type", "status", "model", "provider", "workspace_id"],
            )
            self.routing_latency = Histogram(
                "model_router_routing_latency_seconds",
                "Time taken by prompt analyzer and scoring engine in seconds",
                buckets=[0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
            )
            self.provider_latency = Histogram(
                "model_router_provider_latency_seconds",
                "Time taken by upstream provider inference in seconds",
                ["provider", "model"],
                buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
            )
            self.tokens_total = Counter(
                "model_router_tokens_total",
                "Total input and output tokens processed",
                ["token_type", "model", "provider", "workspace_id"],
            )
            self.cost_dollars_total = Counter(
                "model_router_cost_dollars_total",
                "Total estimated cost of LLM inference in USD",
                ["model", "provider", "workspace_id"],
            )
            self.cost_saved_dollars_total = Counter(
                "model_router_cost_saved_dollars_total",
                "Total estimated cost saved compared to baseline premium models in USD",
                ["workspace_id"],
            )
            self.circuit_breaker_state = Gauge(
                "model_router_circuit_breaker_state",
                "Circuit breaker state per provider (0=CLOSED, 1=HALF_OPEN, 2=OPEN)",
                ["provider"],
            )
            self.active_requests = Gauge(
                "model_router_active_requests",
                "Current number of concurrently processing requests",
            )
        else:
            # Fallback simple internal store
            self._counters: Dict[str, float] = {}

    def record_request(
        self,
        task_type: str,
        status: str,
        model: str,
        provider: str,
        workspace_id: str,
        routing_latency_ms: float,
        provider_latency_ms: float,
        in_tokens: int,
        out_tokens: int,
        cost: float,
        cost_saved: float,
    ):
        if not settings.PROMETHEUS_METRICS_ENABLED:
            return

        ws = workspace_id or "default"
        m = model or "unknown"
        p = provider or "unknown"
        tt = task_type or "GENERAL_QA"
        st = status or "SUCCESS"

        if PROMETHEUS_CLIENT_AVAILABLE:
            try:
                self.requests_total.labels(
                    task_type=tt,
                    status=st,
                    model=m,
                    provider=p,
                    workspace_id=ws,
                ).inc()

                self.routing_latency.observe(max(0.0001, routing_latency_ms / 1000.0))
                self.provider_latency.labels(provider=p, model=m).observe(max(0.001, provider_latency_ms / 1000.0))

                if in_tokens > 0:
                    self.tokens_total.labels(
                        token_type="input", model=m, provider=p, workspace_id=ws
                    ).inc(in_tokens)
                if out_tokens > 0:
                    self.tokens_total.labels(
                        token_type="output", model=m, provider=p, workspace_id=ws
                    ).inc(out_tokens)

                if cost > 0:
                    self.cost_dollars_total.labels(model=m, provider=p, workspace_id=ws).inc(cost)
                if cost_saved > 0:
                    self.cost_saved_dollars_total.labels(workspace_id=ws).inc(cost_saved)
            except Exception:
                pass

    def set_circuit_breaker(self, provider: str, state_str: str):
        if not PROMETHEUS_CLIENT_AVAILABLE or not settings.PROMETHEUS_METRICS_ENABLED:
            return
        val = 0.0
        if state_str == "HALF_OPEN":
            val = 1.0
        elif state_str == "OPEN":
            val = 2.0
        try:
            self.circuit_breaker_state.labels(provider=provider).set(val)
        except Exception:
            pass

    def export_metrics(self) -> Tuple[bytes, str]:
        """
        Exports Prometheus metrics in exposition format.
        Returns (bytes_content, content_type)
        """
        if PROMETHEUS_CLIENT_AVAILABLE:
            return generate_latest(self.registry), CONTENT_TYPE_LATEST

        # Plain text fallback
        fallback = (
            "# HELP model_router_active_requests Current number of active requests\n"
            "# TYPE model_router_active_requests gauge\n"
            "model_router_active_requests 0\n"
        )
        return fallback.encode("utf-8"), "text/plain; version=0.0.4; charset=utf-8"


metrics_collector = MetricsCollector()
