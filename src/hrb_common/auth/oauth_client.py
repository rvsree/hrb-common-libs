"""OAuth2 client-credentials flow, generalized from hrb_chatbot_v2's
auth_client/oauth_client.py (see ROADMAP.md's Phase 8 scope note: the original
hardcodes HRB_LMS_MCP_OAUTH_* env var names - this version takes token_url/
client_id/client_secret as constructor arguments and caches per client_id, so
multiple OAuth2 targets can coexist in one process)."""

import time

import httpx

from hrb_common.observability.logger import get_logger

logger = get_logger("oauth_client")

_token_cache: dict[str, tuple[str, float]] = {}  # client_id -> (token, expires_at)


class OAuth2ClientCredentials:
    def __init__(self, token_url: str, client_id: str, client_secret: str, timeout_seconds: float = 10.0):
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout_seconds = timeout_seconds

    async def get_access_token(self) -> str:
        """Returns a valid Bearer token, fetching a new one if missing or near expiry."""
        cached = _token_cache.get(self.client_id)
        if cached:
            token, expires_at = cached
            if time.monotonic() < expires_at - 30:
                return token

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                self.token_url, json={"client_id": self.client_id, "client_secret": self.client_secret}
            )
            response.raise_for_status()
            body = response.json()

        token = body["access_token"]
        expires_at = time.monotonic() + body["expires_in"]
        _token_cache[self.client_id] = (token, expires_at)
        logger.info("Acquired new OAuth2 access token for client_id=%s, expires_in=%ss", self.client_id, body["expires_in"])
        return token
