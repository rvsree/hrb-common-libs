"""Wraps this project's own ChromaDB/Pinecone clients into LangChain's VectorStore
objects. Ported from hrb_chatbot_v2's db_client/langchain_vector_store.py, import
paths adjusted only, with one necessary substitution: the original resolves its
client via hrb_chatbot_v2's combined db_gateway.get_db_gateway().vector_store(...),
which is out of this package's scope (the db extra is Postgres-only, by design -
see ROADMAP.md's Phase 2 scope correction). _build_vector_db_client() below picks
the provider directly instead, which is all that one call site needed."""

import json

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

from hrb_common.observability.secrets import read_secret
from hrb_common.vectorstore.chroma_client import ChromaDBClient
from hrb_common.vectorstore.pinecone_client import PineconeClient

# The one collection/namespace every provider writes into and reads from -
# shared so a typo in one place can't silently create a second collection.
COLLECTION_NAME = "hrb_chatbot_kb"


class _TextBackfillPineconeIndex:
    """Backfills a "text" metadata key so LangChain's unguarded metadata.pop("text") never raises."""

    def __init__(self, real_index):
        self._real_index = real_index

    def __getattr__(self, name):
        return getattr(self._real_index, name)

    def query(self, *args, **kwargs):
        response = self._real_index.query(*args, **kwargs)
        for match in response.matches:
            if not match.metadata or "text" in match.metadata:
                continue
            match.metadata["text"] = self._extract_text(match.metadata)
        return response

    @staticmethod
    def _extract_text(metadata: dict) -> str:
        if "_node_content" in metadata:
            try:
                return json.loads(metadata["_node_content"]).get("text", "")
            except (json.JSONDecodeError, AttributeError):
                return ""
        if "document" in metadata:
            return metadata["document"]
        return ""


def _build_vector_db_client(vector_db: str | None):
    """Pick the provider client directly by name - replaces the original's
    db_gateway.vector_store(provider=...) call, see the note at top of file."""
    resolved_provider = read_secret("ACTIVE_VECTOR_DB", "chromadb", passed_in_value=vector_db)
    if resolved_provider == "pinecone":
        return PineconeClient()
    return ChromaDBClient()


def get_embeddings(embedding_model: str | None = None) -> OpenAIEmbeddings:
    api_key = read_secret("OPENAI_API_KEY")
    base_url = (read_secret("OPENAI_BASE_URL", "https://api.openai.com/v1") or "").rstrip("/")
    resolved_model = read_secret("OPENAI_EMBED_MODEL", "text-embedding-3-small", passed_in_value=embedding_model)
    return OpenAIEmbeddings(api_key=api_key, base_url=base_url, model=resolved_model)


def get_vector_store(
    vector_db: str | None, embedding_model: str | None = None, collection_name: str = COLLECTION_NAME
):
    """Return (LangChain vector store, resolved provider name) - collection_name lets a test isolate itself."""
    vector_store_client = _build_vector_db_client(vector_db)
    embeddings = get_embeddings(embedding_model)

    if vector_store_client.PROVIDER_NAME == "pinecone":
        wrapped_index = _TextBackfillPineconeIndex(vector_store_client.get_index())
        store = PineconeVectorStore(index=wrapped_index, embedding=embeddings, namespace=collection_name)
    else:
        store = Chroma(
            client=vector_store_client.get_client(),
            collection_name=collection_name,
            embedding_function=embeddings,
        )

    return store, vector_store_client.PROVIDER_NAME
