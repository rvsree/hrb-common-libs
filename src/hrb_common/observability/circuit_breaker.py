"""In-memory circuit breaker, generalizing the real pattern already live in
hrb_chatbot_v2's src/hrb_chatbot/ai/rag_pipeline/tools/mcp_tools/__init__.py
(MCP_CIRCUIT_BREAKER_FAILURE_THRESHOLD = 2, MCP_CIRCUIT_BREAKER_COOLDOWN_SECONDS = 10,
verified against that code directly). That implementation is Postgres-backed and
MCP-specific; this one is in-memory, per-process, and generic - same consecutive-
failure-count + cooldown semantics, not a literal port, and not a formal three-state
(open/half-open/closed) machine - just "skip the call if it's recently failed enough
times," same as the real one."""

import threading
import time


class CircuitOpenError(RuntimeError):
    """Raised instead of attempting a call this breaker has decided is pointless right now."""


class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 2, cooldown_seconds: float = 10.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._lock = threading.Lock()
        self._consecutive_failures = 0
        self._last_failure_at: float | None = None

    def _is_tripped(self) -> bool:
        if self._consecutive_failures < self.failure_threshold:
            return False
        if self._last_failure_at is None:
            return False
        return (time.monotonic() - self._last_failure_at) <= self.cooldown_seconds

    def __enter__(self) -> "CircuitBreaker":
        with self._lock:
            if self._is_tripped():
                age = time.monotonic() - self._last_failure_at
                raise CircuitOpenError(
                    f"{self.name}: known unreachable ({self._consecutive_failures} consecutive "
                    f"failures, last failed {age:.1f}s ago) - skipping until the "
                    f"{self.cooldown_seconds}s cooldown elapses."
                )
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        with self._lock:
            if exc_type is None:
                self._consecutive_failures = 0
                self._last_failure_at = None
            elif exc_type is not CircuitOpenError:
                self._consecutive_failures += 1
                self._last_failure_at = time.monotonic()
        return False  # never swallow the real exception
