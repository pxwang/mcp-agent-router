"""Sync wrapper around the MCP client, so ToolRegistry (a synchronous
dispatcher) can call a tool served over MCP like any other executor.

Opt-in only - see tools.py. Requires mcp_servers/policy_mcp_server.py (and
the REST service it wraps) running separately; see README.md. The `mcp`
package is only imported when this actually runs, so it stays an optional
dependency (the `mcp-demo` extra) rather than a hard requirement for the
default local-only path.
"""

import asyncio
import json
import os

POLICY_MCP_URL = os.environ.get("POLICY_MCP_SERVER_URL", "http://127.0.0.1:8900/mcp")


async def _call_get_policy_status(policy_id: str) -> dict:
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    async with streamable_http_client(POLICY_MCP_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("get_policy_status", {"policy_id": policy_id})
            return json.loads(result.content[0].text)


def call_policy_mcp_tool(policy_id: str) -> dict:
    try:
        return asyncio.run(_call_get_policy_status(policy_id))
    except Exception as e:
        return {"error": f"policy MCP server unreachable at {POLICY_MCP_URL}: {e}"}
