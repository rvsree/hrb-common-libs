import httpx
import pytest
import respx

from hrb_common.auth.oauth_client import OAuth2ClientCredentials, _token_cache


@pytest.fixture(autouse=True)
def clear_token_cache():
    _token_cache.clear()
    yield
    _token_cache.clear()


@respx.mock
async def test_get_access_token_fetches_and_caches():
    respx.post("https://auth.example.com/token").mock(
        return_value=httpx.Response(200, json={"access_token": "tok-abc", "expires_in": 3600})
    )

    client = OAuth2ClientCredentials("https://auth.example.com/token", "client-1", "secret-1")
    token = await client.get_access_token()

    assert token == "tok-abc"
    assert "client-1" in _token_cache


@respx.mock
async def test_get_access_token_reuses_cached_token_without_a_second_call():
    route = respx.post("https://auth.example.com/token").mock(
        return_value=httpx.Response(200, json={"access_token": "tok-abc", "expires_in": 3600})
    )

    client = OAuth2ClientCredentials("https://auth.example.com/token", "client-2", "secret-2")
    await client.get_access_token()
    await client.get_access_token()

    assert route.call_count == 1


async def test_different_client_ids_cache_independently():
    _token_cache["client-a"] = ("token-a", 99999999999.0)
    _token_cache["client-b"] = ("token-b", 99999999999.0)

    client_a = OAuth2ClientCredentials("https://x/token", "client-a", "secret")
    client_b = OAuth2ClientCredentials("https://x/token", "client-b", "secret")

    assert await client_a.get_access_token() == "token-a"
    assert await client_b.get_access_token() == "token-b"
