import pytest

from hrb_common.observability.circuit_breaker import CircuitOpenError
from hrb_common.vectorstore.chroma_client import ChromaDBClient


def test_upsert_and_query_round_trip(tmp_path):
    client = ChromaDBClient(mode="persistent", persist_dir=str(tmp_path), collection_name="test_collection")

    client.upsert(
        "test_collection",
        ids=["chunk-1"],
        documents=["the benefits handbook says dental copay is $20"],
        embeddings=[[0.1, 0.2, 0.3]],
        metadatas=[{"doc_id": "doc-1"}],
    )

    result = client.query("test_collection", query_embedding=[0.1, 0.2, 0.3], top_k=1)
    assert result["ids"][0] == ["chunk-1"]


def test_get_all_chunks_returns_every_chunk(tmp_path):
    client = ChromaDBClient(mode="persistent", persist_dir=str(tmp_path), collection_name="test_collection_2")

    client.upsert("test_collection_2", ids=["a", "b"], documents=["text a", "text b"], embeddings=[[0.1, 0.2], [0.3, 0.4]])

    chunks = client.get_all_chunks("test_collection_2")
    assert len(chunks) == 2
    assert {c["id"] for c in chunks} == {"a", "b"}


def test_delete_removes_chunk(tmp_path):
    client = ChromaDBClient(mode="persistent", persist_dir=str(tmp_path), collection_name="test_collection_3")
    client.upsert("test_collection_3", ids=["x"], documents=["text x"], embeddings=[[0.1]])

    client.delete("test_collection_3", ids=["x"])

    assert client.get_all_chunks("test_collection_3") == []


def test_sanitize_collection_name_enforces_rules():
    assert ChromaDBClient.sanitize_collection_name("My Collection!") == "my_collection"
    assert len(ChromaDBClient.sanitize_collection_name("ab")) >= 3


def test_health_check_reports_healthy(tmp_path):
    client = ChromaDBClient(mode="persistent", persist_dir=str(tmp_path))
    result = client.health_check()
    assert result["status"] == "healthy"


class _FlakyCollection:
    """Fails query() a fixed number of times, then delegates to a real collection."""

    def __init__(self, real_collection, fail_times):
        self._real_collection = real_collection
        self._fail_times = fail_times
        self.call_count = 0

    def query(self, **kwargs):
        self.call_count += 1
        if self.call_count <= self._fail_times:
            raise ConnectionError("transient")
        return self._real_collection.query(**kwargs)


def test_query_retries_a_transient_failure_then_succeeds(tmp_path, monkeypatch):
    client = ChromaDBClient(mode="persistent", persist_dir=str(tmp_path), collection_name="retry_test")
    client.upsert("retry_test", ids=["chunk-1"], documents=["text"], embeddings=[[0.1, 0.2]])
    real_collection = client.get_collection("retry_test")
    flaky = _FlakyCollection(real_collection, fail_times=1)
    monkeypatch.setattr(client, "get_collection", lambda collection_name=None: flaky)

    result = client.query("retry_test", query_embedding=[0.1, 0.2], top_k=1)

    assert result["ids"][0] == ["chunk-1"]
    assert flaky.call_count == 2


def test_query_trips_the_circuit_breaker_after_repeated_failures(tmp_path, monkeypatch):
    client = ChromaDBClient(mode="persistent", persist_dir=str(tmp_path), collection_name="breaker_test")

    def _always_fails(collection_name=None):
        raise ConnectionError("down")

    monkeypatch.setattr(client, "get_collection", _always_fails)

    for _ in range(2):
        with pytest.raises(ConnectionError):
            client.query("breaker_test", query_embedding=[0.1], top_k=1)

    with pytest.raises(CircuitOpenError):
        client.query("breaker_test", query_embedding=[0.1], top_k=1)
