from unittest.mock import AsyncMock, MagicMock, patch

from hrb_common.mcp.client import call_mcp_tool, list_mcp_tools


async def test_call_mcp_tool_opens_session_and_calls_tool():
    fake_session = AsyncMock()
    fake_result = MagicMock()
    fake_result.model_dump.return_value = {"content": [{"type": "text", "text": "leave balance: 10 days"}]}
    fake_session.call_tool.return_value = fake_result

    fake_session_cm = AsyncMock()
    fake_session_cm.__aenter__.return_value = fake_session

    fake_streams_cm = AsyncMock()
    fake_streams_cm.__aenter__.return_value = (MagicMock(), MagicMock(), MagicMock())

    with (
        patch("hrb_common.mcp.client.streamablehttp_client", return_value=fake_streams_cm),
        patch("hrb_common.mcp.client.ClientSession", return_value=fake_session_cm),
    ):
        result = await call_mcp_tool("http://localhost:8190/mcp", "GetLeaveBalance", {"employee_id": "EMP051"})

    fake_session.call_tool.assert_called_once_with("GetLeaveBalance", {"employee_id": "EMP051"})
    assert result["content"][0]["text"] == "leave balance: 10 days"


async def test_list_mcp_tools_returns_tool_list():
    fake_tool = MagicMock()
    fake_tool.model_dump.return_value = {"name": "GetLeaveBalance"}

    fake_session = AsyncMock()
    fake_list_result = MagicMock()
    fake_list_result.tools = [fake_tool]
    fake_session.list_tools.return_value = fake_list_result

    fake_session_cm = AsyncMock()
    fake_session_cm.__aenter__.return_value = fake_session

    fake_streams_cm = AsyncMock()
    fake_streams_cm.__aenter__.return_value = (MagicMock(), MagicMock(), MagicMock())

    with (
        patch("hrb_common.mcp.client.streamablehttp_client", return_value=fake_streams_cm),
        patch("hrb_common.mcp.client.ClientSession", return_value=fake_session_cm),
    ):
        tools = await list_mcp_tools("http://localhost:8190/mcp")

    assert tools == [{"name": "GetLeaveBalance"}]
