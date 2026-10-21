"""Secret/config resolution - same semantics as hrb_chatbot_v2's common.config.settings.read_setting:
passed-in value, then environment, then default. No Secrets Manager SDK call yet - deliberately
out of scope for Phase 1 (see ROADMAP.md) until a consuming service actually needs it in AWS."""

import os


def read_secret(key: str, default: str | None = None, passed_in_value: str | None = None) -> str | None:
    """An empty-string env value counts as unset, same as hrb_chatbot_v2's read_setting."""
    if passed_in_value:
        return passed_in_value

    value_from_env = os.getenv(key)
    if value_from_env:
        return value_from_env

    return default
