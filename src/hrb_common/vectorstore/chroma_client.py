"""ChromaDB client - ported from hrb_chatbot_v2's db_client/chroma_client.py,
import paths adjusted only."""

import re
import threading

import chromadb
from chromadb.config import Settings as ChromaSettings

from hrb_common.observability.call_logger import log_backend_call
from hrb_common.observability.circuit_breaker import CircuitBreaker
from hrb_common.observability.logger import get_logger
from hrb_common.observability.retry import with_retry
from hrb_common.observability.secrets import read_secret
from hrb_common.vectorstore.base_vector_db_client import BaseVectorDBClient

logger = get_logger("chroma_client")

_INVALID_COLLECTION_CHARACTERS = re.compile(r"[^a-zA-Z0-9._-]")


class ChromaDBClient(BaseVectorDBClient):
    PROVIDER_NAME = "chromadb"
    ENV_KEY = "CHROMA_DB_PERSIST_DIR"

    DEFAULT_MODE = "persistent"
    DEFAULT_PERSIST_DIR = "data/chroma_db"
    DEFAULT_HOST = "localhost"
    DEFAULT_PORT = 8000
    DEFAULT_COLLECTION = "default"

    def __init__(self, mode=None, persist_dir=None, host=None, port=None, allow_reset=None, collection_name=None):
        self.mode = read_secret("CHROMA_DB_MODE", self.DEFAULT_MODE, passed_in_value=mode)
        self.persist_dir = read_secret("CHROMA_DB_PERSIST_DIR", self.DEFAULT_PERSIST_DIR, passed_in_value=persist_dir)
        self.host = read_secret("CHROMA_DB_HOST", self.DEFAULT_HOST, passed_in_value=host)
        self.port = int(read_secret("CHROMA_DB_PORT", str(self.DEFAULT_PORT), passed_in_value=str(port) if port else None))

        allow_reset_setting = read_secret("CHROMA_DB_ALLOW_RESET", "false", passed_in_value=allow_reset)
        self.allow_reset = str(allow_reset_setting).strip().lower() in ("1", "true", "yes")

        self.default_collection_name = read_secret("CHROMA_DB_COLLECTION", self.DEFAULT_COLLECTION, passed_in_value=collection_name)

        self._client = None
        self.collection_lock = threading.RLock()  # see hrb_chatbot_v2's Phase 145 note on why RLock, not Lock
        self._circuit_breaker = CircuitBreaker(name="chromadb")

    def get_client(self):
        if self._client is None:
            with self.collection_lock:
                if self._client is None:
                    settings = ChromaSettings(allow_reset=self.allow_reset, anonymized_telemetry=False)
                    if self.mode == "http":
                        logger.info("[CHROMADB] connecting over HTTP to %s:%s", self.host, self.port)
                        self._client = chromadb.HttpClient(host=self.host, port=self.port, settings=settings)
                    else:
                        logger.info("[CHROMADB] using embedded persistent storage at %s", self.persist_dir)
                        self._client = chromadb.PersistentClient(path=self.persist_dir, settings=settings)
        return self._client

    def get_configuration(self) -> dict:
        config = {"mode": self.mode, "collection": self.default_collection_name}
        if self.mode == "http":
            config["host"] = self.host
            config["port"] = self.port
        else:
            config["persist_dir"] = self.persist_dir
        return config

    @staticmethod
    def sanitize_collection_name(name: str) -> str:
        sanitized = _INVALID_COLLECTION_CHARACTERS.sub("_", name).strip("_").lower()
        if len(sanitized) < 3:
            sanitized = (sanitized + "___")[:3]
        return sanitized[:512]

    def get_collection(self, collection_name: str | None = None):
        name = self.sanitize_collection_name(collection_name or self.default_collection_name)
        return self.get_client().get_or_create_collection(name=name)

    def upsert(self, collection_name, ids, documents, embeddings, metadatas=None) -> None:
        @with_retry()
        def _do():
            self.get_collection(collection_name).upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

        with self.collection_lock, self._circuit_breaker, log_backend_call(logger, "chromadb", "vector.upsert", collection=collection_name, chunk_count=len(ids)):
            _do()

    def query(self, collection_name, query_embedding, top_k=5, where=None) -> dict:
        @with_retry()
        def _do():
            return self.get_collection(collection_name).query(query_embeddings=[query_embedding], n_results=top_k, where=where, include=["documents", "metadatas", "distances"])

        with self.collection_lock, self._circuit_breaker, log_backend_call(logger, "chromadb", "vector.query", collection=collection_name, top_k=top_k):
            return _do()

    def delete(self, collection_name, ids) -> None:
        @with_retry()
        def _do():
            self.get_collection(collection_name).delete(ids=ids)

        with self.collection_lock, self._circuit_breaker, log_backend_call(logger, "chromadb", "vector.delete", collection=collection_name, chunk_count=len(ids)):
            _do()

    def update_metadata(self, collection_name, ids, metadatas) -> None:
        @with_retry()
        def _do():
            self.get_collection(collection_name).update(ids=ids, metadatas=metadatas)

        with self.collection_lock, self._circuit_breaker, log_backend_call(logger, "chromadb", "vector.update_metadata", collection=collection_name, chunk_count=len(ids)):
            _do()

    def get_all_chunks(self, collection_name) -> list[dict]:
        @with_retry()
        def _do():
            return self.get_collection(collection_name).get(include=["documents", "metadatas", "embeddings"])

        with self.collection_lock, self._circuit_breaker, log_backend_call(logger, "chromadb", "vector.get_all_chunks", collection=collection_name):
            result = _do()

        embeddings = result.get("embeddings")
        return [
            {"id": chunk_id, "text": document or "", "metadata": metadata or {}, "embedding": list(embeddings[index]) if embeddings is not None else None}
            for index, (chunk_id, document, metadata) in enumerate(zip(result["ids"], result["documents"], result["metadatas"], strict=True))
        ]

    def health_check(self) -> dict:
        result = {"provider": self.PROVIDER_NAME}
        result.update(self.get_configuration())
        try:
            collections = self.get_client().list_collections()
            result["status"] = "healthy"
            result["collections_visible"] = len(collections)
        except Exception as error:
            result["status"] = "unhealthy"
            result["message"] = str(error)
        return result
