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
