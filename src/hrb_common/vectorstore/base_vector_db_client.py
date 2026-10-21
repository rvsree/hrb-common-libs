"""Shared interface every vector database client implements - ported unmodified
from hrb_chatbot_v2's db_client/base_vector_db_client.py."""

from abc import ABC, abstractmethod


class BaseVectorDBClient(ABC):
    PROVIDER_NAME = "base"
    ENV_KEY = ""

    @abstractmethod
    def upsert(self, collection_name: str, ids: list[str], documents: list[str], embeddings: list[list[float]], metadatas: list[dict] | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def query(self, collection_name: str, query_embedding: list[float], top_k: int = 5, where: dict | None = None) -> dict:
        raise NotImplementedError

    @abstractmethod
    def delete(self, collection_name: str, ids: list[str]) -> None:
        raise NotImplementedError

    @abstractmethod
    def update_metadata(self, collection_name: str, ids: list[str], metadatas: list[dict]) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_all_chunks(self, collection_name: str) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> dict:
        raise NotImplementedError
