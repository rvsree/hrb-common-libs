from unittest.mock import MagicMock

import pytest

from hrb_common.llm.openai_client import OpenAIChatClient, OpenAIEmbeddingClient


@pytest.fixture
def chat_client(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    client = OpenAIChatClient()
    client.client = MagicMock()
    return client


def test_ask_returns_answer_text(chat_client):
    fake_response = MagicMock()
    fake_response.choices = [MagicMock(message=MagicMock(content="42"))]
    fake_response.usage = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
    chat_client.client.chat.completions.create.return_value = fake_response

    answer = chat_client.ask("What is the answer?")

    assert answer == "42"
    assert chat_client.last_token_usage == {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}


def test_ask_returns_empty_string_when_content_is_none(chat_client):
    fake_response = MagicMock()
    fake_response.choices = [MagicMock(message=MagicMock(content=None))]
    fake_response.usage = None
    chat_client.client.chat.completions.create.return_value = fake_response

    assert chat_client.ask("anything") == ""


def test_health_check_reports_unhealthy_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = OpenAIChatClient()
    result = client.health_check()
    assert result["status"] == "unhealthy"


def test_embedding_client_get_embeddings_returns_empty_for_empty_input(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    client = OpenAIEmbeddingClient()
    assert client.get_embeddings([]) == []
