"""The "AI enhancement" layer: an MCP server wrapping the existing policy REST
API, unmodified. This is the thin adapter from the earlier discussion - each
tool's implementation is just an HTTP call to one REST endpoint.

Run the REST service first, then this:

    uvicorn services.policy_service:app --port 8800
    python mcp_servers/policy_mcp_server.py
"""

import os

import httpx
from mcp.server.mcpserver import MCPServer

POLICY_SERVICE_URL = os.environ.get("POLICY_SERVICE_URL", "http://127.0.0.1:8800")

mcp = MCPServer("policy")
client = httpx.AsyncClient(base_url=POLICY_SERVICE_URL)


@mcp.tool()
async def get_policy_status(policy_id: str) -> dict:
    """Look up an insurance policy's status, monthly premium, and renewal date.
    Use when the customer asks about their own policy, bill amount, or renewal
    date. Do NOT use for claims or billing disputes."""
    response = await client.get(f"/policies/{policy_id}")
    if response.status_code == 404:
        return {"error": f"Policy {policy_id} not found"}
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8900)
