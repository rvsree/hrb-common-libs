"""Logs the start/duration/outcome of one outbound backend call - a context manager, defined once.
Ported unmodified from hrb_chatbot_v2's common/logging/call_logger.py - behavior must not change.
Phase 17: no change needed here for request_id - logger.py's own _RequestIdFilter already stamps
it on every record from any get_logger()-created logger, including this one's, so adding it to
this file's own extra dict too would just be redundant (the filter overwrites it with the same
value regardless)."""

import time
from collections.abc import Iterator
from contextlib import contextmanager
from logging import Logger


@contextmanager
def log_backend_call(logger: Logger, service: str, operation: str, **context) -> Iterator[None]:
    """Wrap one outbound call with a start/end log - never pass secrets or raw prompt text as context."""
    started_at = time.perf_counter()

    try:
        yield
    except Exception as error:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 1)
        logger.error(
            "[%s] %s failed after %sms (%s): %s",
            service,
            operation,
            duration_ms,
            type(error).__name__,
            error,
            extra={"service": service, "operation": operation, "duration_ms": duration_ms, "status": "error"},
        )
        raise
    else:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 1)
        logger.info(
            "[%s] %s succeeded in %sms - %s",
            service,
            operation,
            duration_ms,
            context,
            extra={"service": service, "operation": operation, "duration_ms": duration_ms, "status": "success"},
        )
