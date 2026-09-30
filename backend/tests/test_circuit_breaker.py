import pytest
import time
from app.fallback.circuit_breaker import CircuitBreakerManager, CircuitBreakerState

def test_circuit_breaker_normal_operation():
    cb = CircuitBreakerManager(failure_threshold=3, cooldown_seconds=60)
    assert cb.is_available("openai") == True
    assert cb.get_state("openai") == CircuitBreakerState.CLOSED

def test_circuit_breaker_failure_trip():
    cb = CircuitBreakerManager(failure_threshold=2, cooldown_seconds=60)
    cb.record_failure("openai")
    assert cb.is_available("openai") == True
    
    cb.record_failure("openai")
    assert cb.get_state("openai") == CircuitBreakerState.OPEN
    assert cb.is_available("openai") == False

def test_circuit_breaker_cooldown_half_open():
    cb = CircuitBreakerManager(failure_threshold=1, cooldown_seconds=0) # 0s cooldown
    cb.record_failure("anthropic")
    assert cb.get_state("anthropic") == CircuitBreakerState.OPEN
    
    time.sleep(0.01) # let cooldown pass
    
    # State should be half-open
    assert cb.get_state("anthropic") == CircuitBreakerState.HALF_OPEN
    
    # First request should be allowed (half-open testing)
    assert cb.is_available("anthropic") == True
    
    # Second request should be blocked (only 1 test allowed)
    assert cb.is_available("anthropic") == False

def test_circuit_breaker_recovery():
    cb = CircuitBreakerManager(failure_threshold=1, cooldown_seconds=0)
    cb.record_failure("gemini")
    time.sleep(0.01)
    
    assert cb.is_available("gemini") == True
    
    # Simulate success
    cb.record_success("gemini")
    
    assert cb.get_state("gemini") == CircuitBreakerState.CLOSED
    assert cb.is_available("gemini") == True

def test_mock_provider_always_available():
    cb = CircuitBreakerManager(failure_threshold=1, cooldown_seconds=60)
    cb.record_failure("mock")
    cb.record_failure("mock")
    
    assert cb.get_state("mock") == CircuitBreakerState.CLOSED
    assert cb.is_available("mock") == True

