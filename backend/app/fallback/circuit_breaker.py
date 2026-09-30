import time
from typing import Dict

class CircuitBreakerState:
    CLOSED = "CLOSED"      # Normal operation, allows requests
    OPEN = "OPEN"          # Failing, blocks requests
    HALF_OPEN = "HALF_OPEN" # Cooldown passed, testing one request


class CircuitBreakerManager:
    """
    Sliding-window circuit breaker for provider health.
    Prevents cascading failures when upstream providers go down.
    """
    def __init__(self, failure_threshold: int = 3, cooldown_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        
        self.failures: Dict[str, int] = {}
        self.last_failure_time: Dict[str, float] = {}
        self.half_open_pending: Dict[str, bool] = {}

    def get_state(self, provider_id: str) -> str:
        # Mock provider is always healthy
        if provider_id == "mock":
            return CircuitBreakerState.CLOSED

        failures = self.failures.get(provider_id, 0)
        if failures < self.failure_threshold:
            return CircuitBreakerState.CLOSED
            
        last_time = self.last_failure_time.get(provider_id, 0.0)
        if time.time() - last_time > self.cooldown_seconds:
            return CircuitBreakerState.HALF_OPEN
            
        return CircuitBreakerState.OPEN

    def is_available(self, provider_id: str) -> bool:
        state = self.get_state(provider_id)
        if state == CircuitBreakerState.CLOSED:
            return True
        if state == CircuitBreakerState.HALF_OPEN:
            if self.half_open_pending.get(provider_id, False):
                return False
            self.half_open_pending[provider_id] = True
            return True
        return False

    def record_success(self, provider_id: str):
        if provider_id in self.failures:
            self.failures[provider_id] = 0
        if provider_id in self.half_open_pending:
            self.half_open_pending[provider_id] = False

    def record_failure(self, provider_id: str):
        if provider_id == "mock":
            return
        self.failures[provider_id] = self.failures.get(provider_id, 0) + 1
        self.last_failure_time[provider_id] = time.time()
        if provider_id in self.half_open_pending:
            self.half_open_pending[provider_id] = False

# Global singleton
circuit_breaker = CircuitBreakerManager()

