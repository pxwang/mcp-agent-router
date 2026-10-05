"""Loads tools.yaml into (a) the tool list for the LLM and (b) the executor map.

Permissions are enforced here, not just in the prompt: a disabled tool is never
exposed to the LLM, and only registered executors are callable.
"""

import os

import yaml

from mcp_agent_router.executors import EXECUTORS
from mcp_agent_router.mcp_client import call_policy_mcp_tool

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "tools.yaml")

# Opt-in: when set to "mcp", get_policy_status is served by the real MCP
# server (mcp_servers/policy_mcp_server.py) wrapping services/policy_service.py,
# instead of the local SQLite-backed executor. Every other tool, and the
# default, is unaffected - see README.md "MCP example".
_POLICY_BACKEND = os.environ.get("MCP_AGENT_ROUTER_POLICY_BACKEND", "local")


class ToolRegistry:
    def __init__(self, config_path: str = _CONFIG_PATH):
        with open(config_path) as f:
            raw = yaml.safe_load(f)

        self._specs = {}
        for entry in raw["tools"]:
            if not entry.get("enabled", True):
                continue
            if entry["name"] not in EXECUTORS:
                raise ValueError(f"No executor registered for tool '{entry['name']}'")
            self._specs[entry["name"]] = entry

    def anthropic_tools(self) -> list[dict]:
        """Tool list in the shape the Anthropic Messages API expects."""
        return [
            {
                "name": spec["name"],
                "description": spec["description"].strip(),
                "input_schema": spec["input_schema"],
            }
            for spec in self._specs.values()
        ]

    def call(self, name: str, arguments: dict) -> dict:
        if name not in self._specs:
            return {"error": f"Unknown or disabled tool '{name}'"}
        if name == "get_policy_status" and _POLICY_BACKEND == "mcp":
            return call_policy_mcp_tool(**arguments)
        return EXECUTORS[name](**arguments)
