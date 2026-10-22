"""Secret/config resolution - same semantics as hrb_chatbot_v2's common.config.settings.read_setting:
passed-in value, then environment, then (Phase 17) a real AWS Secrets Manager call, then default.
Env is checked before Secrets Manager deliberately - this project's own real deployed architecture
(App Runner's RuntimeEnvironmentSecrets) already resolves Secrets-Manager-backed values INTO plain
env vars at container start, so env is the fast, already-proven path there; the direct SDK call is
a fallback for contexts where that injection hasn't happened (local dev with AWS credentials
configured, or a future service reading Secrets Manager directly)."""

import os

import boto3

from hrb_common.observability.logger import get_logger

logger = get_logger("secrets")

# Populated once per process, not re-fetched on every read - a real AWS API
# call on every single settings read would be a real latency/cost problem,
# and a secret's value doesn't need to be re-checked mid-process any more
# than App Runner's own injection (fixed at container start) does.
_secrets_manager_cache: dict[str, str | None] = {}


def _secrets_manager_enabled() -> bool:
    """Defaults off, not on. boto3's own credential-resolution chain takes
    several real seconds to fail when nothing is configured (confirmed live -
    a single test calling read_secret() with no env var set and no AWS
    credentials took ~7s, not a guess) - an always-on fallback would make
    every unset-secret lookup slow by default, everywhere, including every
    test run. A service that actually wants this tier sets the env var."""
    return os.getenv("AWS_SECRETS_MANAGER_ENABLED", "false").strip().lower() == "true"


def _fetch_from_secrets_manager(key: str) -> str | None:
    """Best-effort - disabled by default, or no credentials configured, or
    the secret doesn't exist, or a network error, all degrade to None
    (falls through to the caller's own default), never raises. Same "a
    down/unconfigured backend never breaks the caller" convention every
    other client in this repo already follows."""
    if not _secrets_manager_enabled():
        return None

    if key in _secrets_manager_cache:
        return _secrets_manager_cache[key]

    try:
        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=key)
        value = response.get("SecretString")
    except Exception as error:
        logger.warning("[secrets] Secrets Manager unreachable/unconfigured for %r, skipping: %s", key, error)
        value = None

    _secrets_manager_cache[key] = value
    return value


def read_secret(key: str, default: str | None = None, passed_in_value: str | None = None) -> str | None:
    """An empty-string env value counts as unset, same as hrb_chatbot_v2's read_setting."""
    if passed_in_value:
        return passed_in_value

    value_from_env = os.getenv(key)
    if value_from_env:
        return value_from_env

    value_from_secrets_manager = _fetch_from_secrets_manager(key)
    if value_from_secrets_manager:
        return value_from_secrets_manager

    return default
