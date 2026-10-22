from unittest.mock import MagicMock, patch

from hrb_common.llm.bedrock_client import BedrockChatClient


def _build_client():
    with patch("boto3.client") as fake_boto_client:
        fake_boto_client.return_value = MagicMock()
        client = BedrockChatClient(region="us-east-1", access_key_id="id", secret_access_key="secret")
    return client


def test_get_configuration_reports_explicit_credentials():
    client = _build_client()
    config = client.get_configuration()
    assert config["credentials_source"] == "explicit .env values"


def test_ask_joins_text_blocks():
    client = _build_client()
    client.client.converse.return_value = {
        "output": {"message": {"content": [{"text": "42"}]}},
    }

    answer = client.ask("What is the answer?")

    assert answer == "42"


def test_convert_tools_to_bedrock_format_drops_non_function_tools():
    tools = [{"type": "function", "function": {"name": "lookup", "description": "", "parameters": {}}}]
    bedrock_tools = BedrockChatClient._convert_tools_to_bedrock_format(tools)
    assert bedrock_tools == [{"toolSpec": {"name": "lookup", "description": "", "inputSchema": {"json": {}}}}]


def test_convert_messages_to_bedrock_format_separates_system_message():
    messages = [{"role": "system", "content": "be nice"}, {"role": "user", "content": "hi"}]
    system_text, bedrock_messages = BedrockChatClient._convert_messages_to_bedrock_format(messages)
    assert system_text == "be nice"
    assert bedrock_messages == [{"role": "user", "content": [{"text": "hi"}]}]


def test_health_check_reports_unhealthy_on_boto_error():
    client = _build_client()
    with patch("boto3.client", side_effect=RuntimeError("no credentials")):
        result = client.health_check()
    assert result["status"] == "unhealthy"
