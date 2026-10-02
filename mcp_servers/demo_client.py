"""Proves the loop end-to-end: a plain MCP client discovers and calls the
tool exposed by policy_mcp_server.py, which itself calls the existing REST
API. Nothing here is specific to Claude or any particular LLM - this is
exactly what an LLM's tool-calling runtime does under the hood.

Run both servers first (see their docstrings), then:

    python mcp_servers/demo_client.py
"""

import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

MCP_SERVER_URL = "http://127.0.0.1:8900/mcp"


async def main() -> None:
    async with streamable_http_client(MCP_SERVER_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Discovered tools:", [t.name for t in tools.tools])

            result = await session.call_tool("get_policy_status", {"policy_id": "P-1234"})
            print("get_policy_status(P-1234) ->", result.content)

            result = await session.call_tool("get_policy_status", {"policy_id": "P-0000"})
            print("get_policy_status(P-0000) ->", result.content)


if __name__ == "__main__":
    asyncio.run(main())
