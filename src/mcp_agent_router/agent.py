"""LLM tool-calling loop over the tool registry."""

import json
import os
import time

import anthropic

from mcp_agent_router.audit import log_tool_call
from mcp_agent_router.tools import ToolRegistry

MAX_TOOL_ROUNDS = 5

SYSTEM_PROMPT = """You are a support assistant for a mock insurance company.
Use the available tools to answer questions about policies, scheduling, and FAQs.
Ask a clarifying question when a required parameter (like a policy ID) is missing -
never guess personal data. Keep answers short and in plain language."""


class Agent:
    def __init__(self, model: str | None = None, registry: ToolRegistry | None = None):
        self.client = anthropic.Anthropic()
        self.model = model or os.environ.get("MCP_AGENT_ROUTER_MODEL", "claude-sonnet-5")
        self.registry = registry or ToolRegistry()
        self.messages: list[dict] = []

    def reset(self) -> None:
        self.messages = []

    def send(self, user_text: str) -> str:
        self.messages.append({"role": "user", "content": user_text})

        for _ in range(MAX_TOOL_ROUNDS):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=self.registry.anthropic_tools(),
                messages=self.messages,
            )
            self.messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                return _text_of(response.content)

            tool_results = [self._run_tool(block, user_text) for block in response.content if block.type == "tool_use"]
            self.messages.append({"role": "user", "content": tool_results})

        return "I wasn't able to finish that within the allowed number of tool calls. Let me hand you off to a human agent."

    def _run_tool(self, block, query: str) -> dict:
        start = time.perf_counter()
        result = self.registry.call(block.name, block.input)
        latency_ms = (time.perf_counter() - start) * 1000

        error = result.get("error") if isinstance(result, dict) else None
        log_tool_call(
            query=query,
            tool_name=block.name,
            arguments=block.input,
            latency_ms=latency_ms,
            success=error is None,
            error=error,
        )

        return {
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": json.dumps(result),
        }


def _text_of(content_blocks) -> str:
    return "".join(b.text for b in content_blocks if b.type == "text")
