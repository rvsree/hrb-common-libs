"""Generic Redis connection + key-naming convention - new code, not an extraction
(hrb_chatbot_v2's cache_client/ has no generic connector, just two feature-specific
caches). Key convention matches the one already fixed in the NFR Components doc."""

import redis

from hrb_common.observability.secrets import read_secret


def get_redis_client(url: str | None = None) -> redis.Redis:
    resolved_url = url or read_secret("REDIS_URL", "redis://localhost:6379/0")
    return redis.from_url(resolved_url, decode_responses=True)


def build_cache_key(service: str, purpose: str, content_hash: str) -> str:
    """{service}:{purpose}:{content_hash} - so independent services' cache keys
    never collide in the same Redis instance."""
    return f"{service}:{purpose}:{content_hash}"
