from unittest.mock import MagicMock

import pytest

from hrb_common.llm.anthropic_client import AnthropicChatClient


@pytest.fixture
def chat_client(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client = AnthropicChatClient()
    client.client = MagicMock()
    return client


def test_ask_joins_text_blocks(chat_client):
    fake_response = MagicMock()
    fake_response.content = [MagicMock(type="text", text="42")]
    fake_response.usage = MagicMock(input_tokens=10, output_tokens=5)
    chat_client.client.messages.create.return_value = fake_response

    answer = chat_client.ask("What is the answer?")

    assert answer == "42"


def test_health_check_reports_unhealthy_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    client = AnthropicChatClient()
    result = client.health_check()
    assert result["status"] == "unhealthy"


def test_convert_tools_to_claude_format_drops_non_function_tools():
    tools = [{"type": "function", "function": {"name": "lookup", "description": "", "parameters": {}}}]
    claude_tools = AnthropicChatClient.convert_tools_to_claude_format(tools)
    assert claude_tools == [{"name": "lookup", "description": "", "input_schema": {}}]


def test_split_out_system_message_separates_system_role():
    messages = [{"role": "system", "content": "be nice"}, {"role": "user", "content": "hi"}]
    system_text, remaining = AnthropicChatClient.split_out_system_message(messages)
    assert system_text == "be nice"
    assert remaining == [{"role": "user", "content": "hi"}]


def test_convert_response_to_openai_format_reports_tool_calls():
    fake_response = MagicMock()
    tool_use_block = MagicMock(type="tool_use", id="call-1", input={"q": "x"})
    tool_use_block.name = "lookup"
    fake_response.content = [tool_use_block]
    fake_response.usage = MagicMock(input_tokens=10, output_tokens=5)

    converted = AnthropicChatClient.convert_response_to_openai_format(fake_response)

    tool_calls = converted["choices"][0]["message"]["tool_calls"]
    assert tool_calls[0]["function"]["name"] == "lookup"
