from hrb_common.vectorstore.chroma_client import ChromaDBClient
from hrb_common.vectorstore.langchain_vector_store import _build_vector_db_client, get_embeddings, get_vector_store
from hrb_common.vectorstore.pinecone_client import PineconeClient


def test_build_vector_db_client_defaults_to_chroma(monkeypatch):
    monkeypatch.delenv("ACTIVE_VECTOR_DB", raising=False)
    assert isinstance(_build_vector_db_client(None), ChromaDBClient)


def test_build_vector_db_client_selects_pinecone_by_name(monkeypatch):
    monkeypatch.setenv("PINECONE_API_KEY", "test-key")
    assert isinstance(_build_vector_db_client("pinecone"), PineconeClient)


def test_get_embeddings_uses_resolved_model(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    embeddings = get_embeddings("text-embedding-3-large")
    assert embeddings.model == "text-embedding-3-large"


def test_get_vector_store_returns_chroma_and_provider_name(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("CHROMA_DB_PERSIST_DIR", str(tmp_path))
    monkeypatch.delenv("ACTIVE_VECTOR_DB", raising=False)

    store, provider_name = get_vector_store(None, collection_name="test_collection")

    assert provider_name == "chromadb"
    assert store is not None
