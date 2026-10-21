from hrb_common.db.connection import PostgresConnectionConfig, qualify


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
