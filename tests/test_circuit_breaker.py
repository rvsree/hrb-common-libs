import time

import pytest

from hrb_common.observability.circuit_breaker import CircuitBreaker, CircuitOpenError


def test_circuit_breaker_allows_calls_while_healthy():
    breaker = CircuitBreaker("test_service", failure_threshold=2, cooldown_seconds=10)

    with breaker:
        pass  # a successful call

    with breaker:
        pass  # still healthy

    # no exception raised means the breaker never tripped


def test_circuit_breaker_trips_after_failure_threshold_within_cooldown():
    breaker = CircuitBreaker("test_service", failure_threshold=2, cooldown_seconds=10)

    for _ in range(2):
        with pytest.raises(ValueError):
            with breaker:
                raise ValueError("downstream failed")

    with pytest.raises(CircuitOpenError):
        with breaker:
            pass


def test_circuit_breaker_resets_after_a_success():
    breaker = CircuitBreaker("test_service", failure_threshold=2, cooldown_seconds=10)

    with pytest.raises(ValueError):
        with breaker:
            raise ValueError("one failure, not enough to trip")

    with breaker:
        pass  # a success resets the consecutive-failure count

    with pytest.raises(ValueError):
        with breaker:
            raise ValueError("one more failure - still below threshold since the count reset")

    with breaker:
        pass  # should not raise CircuitOpenError - never reached 2 consecutive failures


def test_circuit_breaker_recovers_after_cooldown_elapses():
    breaker = CircuitBreaker("test_service", failure_threshold=1, cooldown_seconds=0.05)

    with pytest.raises(ValueError):
        with breaker:
            raise ValueError("trips immediately with threshold=1")

    with pytest.raises(CircuitOpenError):
        with breaker:
            pass

    time.sleep(0.1)  # longer than the 0.05s cooldown

    with breaker:
        pass  # cooldown elapsed - breaker allows the call through again
