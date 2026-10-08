import time
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager, contextmanager
from app.config.settings import get_settings

settings = get_settings()

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False


class RouterTracer:
    """
    OpenTelemetry distributed tracing manager for AI Model Router.
    Tracks spans for Analyzer, Scoring Engine, Provider Dispatch, and Circuit Breaker.
    """

    def __init__(self):
        self._tracer = None
        self._init_otel()

    def _init_otel(self):
        if not OPENTELEMETRY_AVAILABLE or not settings.OTEL_ENABLED:
            return

        try:
            resource = Resource.create({"service.name": settings.OTEL_SERVICE_NAME})
            provider = TracerProvider(resource=resource)
            
            if settings.OTEL_EXPORTER_OTLP_ENDPOINT:
                try:
                    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                    exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT)
                    provider.add_span_processor(BatchSpanProcessor(exporter))
                except Exception:
                    pass

            trace.set_tracer_provider(provider)
            self._tracer = trace.get_tracer("model_router")
        except Exception:
            self._tracer = None

    @contextmanager
    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Synchronous span context manager."""
        t0 = time.perf_counter()
        if self._tracer:
            with self._tracer.start_as_current_span(name) as span:
                if attributes:
                    for k, v in attributes.items():
                        span.set_attribute(k, str(v))
                try:
                    yield span
                finally:
                    span.set_attribute("duration_ms", (time.perf_counter() - t0) * 1000.0)
        else:
            # Standalone fallback span
            span_obj = {"name": name, "attributes": attributes or {}}
            try:
                yield span_obj
            finally:
                span_obj["duration_ms"] = (time.perf_counter() - t0) * 1000.0

    @asynccontextmanager
    async def start_async_span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Asynchronous span context manager."""
        t0 = time.perf_counter()
        if self._tracer:
            with self._tracer.start_as_current_span(name) as span:
                if attributes:
                    for k, v in attributes.items():
                        span.set_attribute(k, str(v))
                try:
                    yield span
                finally:
                    span.set_attribute("duration_ms", (time.perf_counter() - t0) * 1000.0)
        else:
            span_obj = {"name": name, "attributes": attributes or {}}
            try:
                yield span_obj
            finally:
                span_obj["duration_ms"] = (time.perf_counter() - t0) * 1000.0


router_tracer = RouterTracer()
