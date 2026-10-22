"""Sets up logging so every file prints messages the same way - get_logger(name) factory.
Ported from hrb_chatbot_v2's common/logging/logger.py - same shape, this repo's own import path.
Phase 17: every log line also carries request_id, read from request_context.py's contextvar -
"-" when none is set (a background job, or a request RequestIdMiddleware hasn't touched yet)."""

import logging
import sys

from hrb_common.observability.request_context import get_request_id

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | [%(request_id)s] | %(message)s"
TIME_FORMAT = "%H:%M:%S"


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        return True


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Return a logger with the given name, setting it up on first use - safe to call repeatedly."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=TIME_FORMAT))
    handler.addFilter(_RequestIdFilter())

    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False

    return logger
