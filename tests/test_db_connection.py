import pytest

from hrb_common.db import connection
from hrb_common.db.connection import PostgresConnectionConfig, get_connection, qualify
from hrb_common.observability.circuit_breaker import CircuitOpenError


def test_qualify_quotes_schema_and_table():
    assert qualify("rag_ingestion", "documents") == '"rag_ingestion"."documents"'


def test_config_from_env_reads_settings(monkeypatch):
    monkeypatch.setenv("POSTGRES_DB_HOST", "myhost")
    monkeypatch.setenv("POSTGRES_DB_PORT", "5433")
    monkeypatch.setenv("POSTGRES_DB_NAME", "mydb")
    monkeypatch.setenv("POSTGRES_DB_USER", "myuser")
    monkeypatch.setenv("POSTGRES_DB_PASSWORD", "mypass")

    config = PostgresConnectionConfig.from_env()

    assert config.host == "myhost"
    assert config.port == "5433"
    assert config.dbname == "mydb"
    assert config.user == "myuser"
    assert config.password == "mypass"


@pytest.fixture(autouse=True)
def _reset_module_circuit_breaker():
    """get_connection()'s breaker is a module-level singleton (see connection.py's
    own reasoning) - reset its state between tests so one test's failures don't
    trip the breaker for the next one."""
    connection._connection_circuit_breaker._consecutive_failures = 0
    connection._connection_circuit_breaker._last_failure_at = None
    yield
    connection._connection_circuit_breaker._consecutive_failures = 0
    connection._connection_circuit_breaker._last_failure_at = None


def test_get_connection_retries_a_transient_failure_then_succeeds(monkeypatch):
    call_count = {"n": 0}
    fake_connection = object()

    def _fake_connect(**kwargs):
        call_count["n"] += 1
        if call_count["n"] < 2:
            raise ConnectionError("transient")
        return fake_connection

    monkeypatch.setattr(connection.psycopg, "connect", _fake_connect)

    result = get_connection(PostgresConnectionConfig("h", "5432", "db", "u", "p"))

    assert result is fake_connection
    assert call_count["n"] == 2


def test_get_connection_trips_the_circuit_breaker_after_repeated_failures(monkeypatch):
    call_count = {"n": 0}

    def _always_fails(**kwargs):
        call_count["n"] += 1
        raise ConnectionError("down")

    monkeypatch.setattr(connection.psycopg, "connect", _always_fails)
    config = PostgresConnectionConfig("h", "5432", "db", "u", "p")

    for _ in range(2):
        with pytest.raises(ConnectionError):
            get_connection(config)

    calls_before_third_attempt = call_count["n"]
    with pytest.raises(CircuitOpenError):
        get_connection(config)

    assert call_count["n"] == calls_before_third_attempt
