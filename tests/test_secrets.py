from unittest.mock import MagicMock, patch

from hrb_common.observability import secrets
from hrb_common.observability.secrets import read_secret


def test_read_secret_prefers_passed_in_value(monkeypatch):
    monkeypatch.setenv("MY_KEY", "from_env")
    assert read_secret("MY_KEY", default="from_default", passed_in_value="from_arg") == "from_arg"


def test_read_secret_falls_back_to_env(monkeypatch):
    monkeypatch.setenv("MY_KEY", "from_env")
    assert read_secret("MY_KEY", default="from_default") == "from_env"


def test_read_secret_falls_back_to_default_when_unset(monkeypatch):
    monkeypatch.delenv("MY_KEY", raising=False)
    assert read_secret("MY_KEY", default="from_default") == "from_default"


def test_read_secret_treats_empty_env_as_unset(monkeypatch):
    monkeypatch.setenv("MY_KEY", "")
    assert read_secret("MY_KEY", default="from_default") == "from_default"


def _clear_cache():
    secrets._secrets_manager_cache.clear()


def test_secrets_manager_is_disabled_by_default(monkeypatch):
    """Confirms the opt-in gate - boto3.client must NOT even be called when
    AWS_SECRETS_MANAGER_ENABLED isn't set, since a real (uncached) call
    takes several real seconds to fail when nothing is configured (found
    live during this phase's own implementation, not assumed)."""
    monkeypatch.delenv("AWS_SECRETS_MANAGER_ENABLED", raising=False)
    monkeypatch.delenv("MY_KEY", raising=False)
    _clear_cache()

    def _should_not_be_called(*args, **kwargs):
        raise AssertionError("boto3.client must not be called when Secrets Manager is disabled")

    with patch("boto3.client", _should_not_be_called):
        assert read_secret("MY_KEY", default="from_default") == "from_default"


def test_secrets_manager_used_when_enabled_and_env_unset(monkeypatch):
    monkeypatch.setenv("AWS_SECRETS_MANAGER_ENABLED", "true")
    monkeypatch.delenv("MY_KEY", raising=False)
    _clear_cache()
    fake_client = MagicMock()
    fake_client.get_secret_value.return_value = {"SecretString": "from_secrets_manager"}

    with patch("boto3.client", return_value=fake_client):
        result = read_secret("MY_KEY", default="from_default")

    assert result == "from_secrets_manager"
    fake_client.get_secret_value.assert_called_once_with(SecretId="MY_KEY")


def test_secrets_manager_result_is_cached_not_fetched_twice(monkeypatch):
    monkeypatch.setenv("AWS_SECRETS_MANAGER_ENABLED", "true")
    monkeypatch.delenv("MY_KEY", raising=False)
    _clear_cache()
    fake_client = MagicMock()
    fake_client.get_secret_value.return_value = {"SecretString": "cached_value"}

    with patch("boto3.client", return_value=fake_client):
        read_secret("MY_KEY", default="from_default")
        read_secret("MY_KEY", default="from_default")

    fake_client.get_secret_value.assert_called_once()


def test_secrets_manager_failure_falls_back_to_default_not_raise(monkeypatch):
    monkeypatch.setenv("AWS_SECRETS_MANAGER_ENABLED", "true")
    monkeypatch.delenv("MY_KEY", raising=False)
    _clear_cache()

    def _raises(*args, **kwargs):
        raise RuntimeError("no credentials configured")

    with patch("boto3.client", _raises):
        result = read_secret("MY_KEY", default="from_default")

    assert result == "from_default"
