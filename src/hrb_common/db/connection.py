"""Generic Postgres connection helper - new code, not an extraction (see ROADMAP.md's
Phase 2 scope note: hrb_chatbot_v2's db_client/ has no generic connector to port,
just the same psycopg.connect(...) pattern copy-pasted per feature store)."""

from dataclasses import dataclass

import psycopg

from hrb_common.observability.circuit_breaker import CircuitBreaker
from hrb_common.observability.retry import with_retry
from hrb_common.observability.secrets import read_secret

# Module-level, not per-call - a fresh CircuitBreaker() per call would never
# accumulate consecutive failures, same reasoning as a class's own self._circuit_breaker.
_connection_circuit_breaker = CircuitBreaker(name="postgres")


@dataclass
class PostgresConnectionConfig:
    host: str
    port: str
    dbname: str
    user: str
    password: str

    @classmethod
    def from_env(cls) -> "PostgresConnectionConfig":
        return cls(
            host=read_secret("POSTGRES_DB_HOST", ""),
            port=read_secret("POSTGRES_DB_PORT", "5432"),
            dbname=read_secret("POSTGRES_DB_NAME", ""),
            user=read_secret("POSTGRES_DB_USER", ""),
            password=read_secret("POSTGRES_DB_PASSWORD", ""),
        )


def get_connection(config: PostgresConnectionConfig | None = None) -> psycopg.Connection:
    """One real connection - callers wrap with asyncio.to_thread() for async code,
    same convention every hrb_chatbot_v2 store already follows. Retries transient
    connect failures (3 attempts, exponential backoff); a Postgres known-down from
    repeated recent failures fails fast via CircuitOpenError instead."""
    config = config or PostgresConnectionConfig.from_env()

    @with_retry()
    def _connect() -> psycopg.Connection:
        return psycopg.connect(
            host=config.host, port=config.port, dbname=config.dbname, user=config.user, password=config.password
        )

    with _connection_circuit_breaker:
        return _connect()


def qualify(schema: str, table: str) -> str:
    """Schema-qualified, quoted identifier - "schema"."table" - for the schema-per-domain
    convention hrb_chatbot_v2's own schema migration establishes (rag_ingestion,
    rag_retrieval, platform_*, ...)."""
    return f'"{schema}"."{table}"'
