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
