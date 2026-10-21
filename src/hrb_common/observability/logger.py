"""Sets up logging so every file prints messages the same way - get_logger(name) factory.
Ported from hrb_chatbot_v2's common/logging/logger.py - same shape, this repo's own import path."""

import logging
import sys

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
TIME_FORMAT = "%H:%M:%S"


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Return a logger with the given name, setting it up on first use - safe to call repeatedly."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=TIME_FORMAT))

    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False

    return logger
