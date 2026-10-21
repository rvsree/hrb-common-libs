from hrb_common.cache.connection import build_cache_key, get_redis_client


def test_build_cache_key_shape():
    assert build_cache_key("rag_retrieval_service", "answer_cache", "abc123") == "rag_retrieval_service:answer_cache:abc123"


def test_get_redis_client_uses_passed_url():
    client = get_redis_client(url="redis://localhost:6379/1")
    assert client.connection_pool.connection_kwargs["db"] == 1


def test_get_redis_client_falls_back_to_default(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    client = get_redis_client()
    assert client.connection_pool.connection_kwargs["host"] == "localhost"
