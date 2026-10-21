"""Retry/backoff wrapper for outbound calls to Postgres, a vector store, an LLM
provider, or another service - a safety net, so its own overhead must stay small."""

from collections.abc import Callable
from typing import TypeVar

from tenacity import retry, stop_after_attempt, wait_exponential

T = TypeVar("T")


def with_retry(
    max_attempts: int = 3, backoff_base_seconds: float = 0.5
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Exponential backoff starting at backoff_base_seconds, max_attempts total tries
    (the first try plus max_attempts - 1 retries). Defaults match the NFR Components
    spec's documented default - override per call site, never blanket-raise it."""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=backoff_base_seconds, min=backoff_base_seconds),
        reraise=True,
    )
