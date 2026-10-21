"""Carries the current request's request_id across a call chain within one process,
so every log line and outbound call for one request can tag itself consistently."""

import uuid
from contextvars import ContextVar

_request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def new_request_id() -> str:
    """A fresh id for a request that didn't arrive with one already."""
    return uuid.uuid4().hex


def set_request_id(request_id: str) -> None:
    _request_id_var.set(request_id)


def get_request_id() -> str | None:
    """None means no request_id has been set in this context yet - callers decide
    whether that's an error or just means "not inside a request" (e.g. a background job)."""
    return _request_id_var.get()
