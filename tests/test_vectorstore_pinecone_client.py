from unittest.mock import MagicMock

import pytest

from hrb_common.vectorstore.pinecone_client import PineconeClient, _text_from_llama_index_node_content


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("PINECONE_API_KEY", "test-key")
    monkeypatch.setenv("PINECONE_INDEX_NAME", "test-index")
    pinecone_client = PineconeClient()
    pinecone_client._client = MagicMock()
    pinecone_client._index_ready = True
    pinecone_client._index = MagicMock()
    return pinecone_client


def test_upsert_builds_vectors_with_document_in_metadata(client):
    client.upsert("ns", ids=["a"], documents=["hello"], embeddings=[[0.1, 0.2]], metadatas=[{"doc_id": "d1"}])

    client._index.upsert.assert_called_once()
    vectors = client._index.upsert.call_args.kwargs["vectors"]
    assert vectors == [{"id": "a", "values": [0.1, 0.2], "metadata": {"doc_id": "d1", "document": "hello"}}]


def test_query_returns_chroma_shaped_result(client):
    fake_match = MagicMock(id="a", score=0.9, metadata={"document": "hello"})
    client._index.query.return_value = MagicMock(matches=[fake_match])

    result = client.query("ns", query_embedding=[0.1], top_k=1)

    assert result["ids"] == [["a"]]
    assert result["documents"] == [["hello"]]
    assert result["distances"] == [[0.9]]


def test_delete_calls_index_delete(client):
    client.delete("ns", ids=["a"])
    client._index.delete.assert_called_once_with(ids=["a"], namespace="ns")


def test_health_check_reports_unhealthy_without_api_key(monkeypatch):
    monkeypatch.delenv("PINECONE_API_KEY", raising=False)
    client = PineconeClient()
    result = client.health_check()
    assert result["status"] == "unhealthy"


def test_text_from_llama_index_node_content_handles_missing_key():
    assert _text_from_llama_index_node_content({}) == ""


def test_text_from_llama_index_node_content_parses_blob():
    metadata = {"_node_content": '{"text": "chunk text"}'}
    assert _text_from_llama_index_node_content(metadata) == "chunk text"
