import json
import logging
from typing import Dict, Any, Optional
import datetime
from app.storage.redis_client import publish_traffic_event
from app.observability.metrics import metrics_collector
import asyncio

logger = logging.getLogger("model_router.observability")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('{"time":"%(asctime)s", "level":"%(levelname)s", "event":%(message)s}')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def log_router_event(
    event_name: str,
    request_id: str,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    duration_ms: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Structured event logger for model router pipeline.
    Redacts sensitive credentials automatically and publishes to Redis & Prometheus.
    """
    payload = {
        "event": event_name,
        "request_id": request_id,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "model": model,
        "provider": provider,
        "duration_ms": duration_ms,
    }
    if metadata:
        # Sanitize any key that looks like an API token
        safe_meta = {
            k: ("[REDACTED]" if "key" in k.lower() or "secret" in k.lower() or "token" in k.lower() and "count" not in k.lower() else v)
            for k, v in metadata.items()
        }
        payload["metadata"] = safe_meta

        # Record Prometheus Metrics if request completed
        if "request_completed" in event_name:
            metrics_collector.record_request(
                task_type=metadata.get("task_type", "GENERAL_QA"),
                status=metadata.get("status", "SUCCESS"),
                model=model or "unknown",
                provider=provider or "unknown",
                workspace_id=metadata.get("workspace_id", "default"),
                routing_latency_ms=metadata.get("routing_latency_ms", 0.0),
                provider_latency_ms=duration_ms or 0.0,
                in_tokens=metadata.get("in_tokens", 0),
                out_tokens=metadata.get("out_tokens", 0),
                cost=metadata.get("cost", 0.0),
                cost_saved=metadata.get("cost_saved", 0.0),
            )

    logger.info(json.dumps(payload))
    
    # Fire and forget Redis publish
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(publish_traffic_event(payload))
    except RuntimeError:
        pass # No running loop
