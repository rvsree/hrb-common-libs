"""Generic MCP tool-calling - new, generalized code (see ROADMAP.md's Phase 5 scope
note: hrb_chatbot_v2's mcp_client/ folder is empty; the real logic lives in
ai/rag_pipeline/tools/mcp_tools/__init__.py mixed with leave-balance-specific keyword
routing and a Postgres-backed circuit breaker - both excluded here. Use this
package's own CircuitBreaker (hrb_common.observability) around a call if needed."""

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from hrb_common.observability.logger import get_logger

logger = get_logger("mcp_client")


async def call_mcp_tool(server_url: str, tool_name: str, arguments: dict, access_token: str | None = None) -> dict:
    """Opens one MCP session, calls one tool, closes it - raises on failure, same as
    hrb_chatbot_v2's _call_mcp_tool(), without that function's keyword-routing/circuit-breaker."""
    headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}

    async with streamablehttp_client(server_url, headers=headers) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return result.model_dump()


async def list_mcp_tools(server_url: str, access_token: str | None = None) -> list[dict]:
    """Real list_tools() discovery - same pattern hrb_chatbot_v2's Phase 239 used."""
    headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}

    async with streamablehttp_client(server_url, headers=headers) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.list_tools()
            return [tool.model_dump() for tool in result.tools]
