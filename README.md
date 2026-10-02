# mcp-agent-router

An AI chat agent that routes requests to domain services via LLM tool calling, MCP servers, and RAG. See [PROJECT_PLAN.md](PROJECT_PLAN.md) for the full design and build plan.

## Status

**Step 1 of the build plan:** a text-only tool-calling agent with 3 mock tools
(`get_policy_status`, `schedule_appointment`, `search_faq`) backed by SQLite.
Tools are defined in a config-driven registry (`src/mcp_agent_router/config/tools.yaml`)
rather than hardcoded, so the next step (moving them behind MCP servers) is a drop-in change.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export ANTHROPIC_API_KEY=sk-ant-...
```

## Run

```bash
mcp-agent-router
# or: python -m mcp_agent_router.cli
```

```
you> What's the status of policy P-1234?
agent> Policy P-1234 is active, with a $142.50 monthly premium, renewing 2027-01-01.
```

## Test

```bash
pytest
```

Tests cover the tool executors and the registry; they don't call the Anthropic API.

## Layout

```
src/mcp_agent_router/
  config/tools.yaml   # tool registry: name, description, domain, owner, schema, permissions
  db.py               # SQLite mock data (policies, appointments, faq_entries)
  executors.py        # tool implementations
  tools.py            # loads tools.yaml -> LLM tool list + executor dispatch
  agent.py            # tool-calling loop (Anthropic Messages API)
  cli.py              # interactive REPL
evals/routing_evals.jsonl  # utterance -> expected tool(s), for routing evals (step 5)
```
