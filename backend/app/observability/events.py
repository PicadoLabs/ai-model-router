import json
import logging
from typing import Dict, Any, Optional
import datetime

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
    Redacts sensitive credentials automatically.
    """
    payload = {
        "event": event_name,
        "request_id": request_id,
        "timestamp": datetime.datetime.utcnow().isoformat(),
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

    logger.info(json.dumps(payload))
