# mcp-agent-router: AI chat agent with LLM routing + MCP tools (voice optional, phase 2)

**Repo:** github.com/pxwang/mcp-agent-router (planned) · **Local folder:** ~/work/mcp-agent-router (separate from ~/cv; use its own Claude session)
**Tagline:** An AI chat agent that routes requests to domain services via LLM tool calling, MCP servers, and RAG.

*Saved Oct 1, 2026. A portfolio project to pair with the ArXiv RAG project (github.com/pxwang/arxiv-paper-qa). It shows agentic AI, tool calling and MCP for AI-engineering and data-and-AI roles.*

## Decision (Oct 1, 2026)
**Build it as a text chat agent first.** Routing, MCP tools, RAG, guardrails and evals are the core and identical for text and voice. Voice (VAD, STT, TTS, barge-in, latency under 1 second) is an optional **phase 2** wrapper, e.g. Pipecat around the same agent. Text is simpler to build and test, and it's how most enterprise agents ship today.

## Goal
A small working voice assistant, for example for a mock insurance company: the user speaks, the system understands, routes to the right domain service(s), and answers by voice.

## Architecture (cascaded pipeline)
```
User voice ─► Browser mic / WebRTC (streaming audio)
   ▼
[1] VAD + turn detection (speech start/end, barge-in)
   ▼
[2] Streaming speech-to-text (partial transcripts)
   ▼
[3] Agent / orchestrator (LLM)
     ├─ session state & memory
     ├─ routing = LLM tool calling (or fast classifier → LLM fallback)
     ├─ tools via MCP servers ──► domain services (policy, billing, scheduling)
     ├─ RAG ──► FAQ/policy docs (hybrid search + re-rank, reuse arxiv-paper-qa)
     └─ guardrails (identity check, PII redaction, allowed actions, human handoff)
   ▼ response text (streamed, written for speech)
[4] Streaming text-to-speech ─► user   (stop immediately if the user interrupts)
Side: tracing/logging, latency per stage, routing evals, cost per call
```

## Routing options (pick one, compare later)
1. **Tool calling:** the LLM picks tools and arguments; handles multi-domain requests in one turn.
2. **Router → specialist agents:** a small fast model returns JSON `{domains, confidence}`; each specialist has a focused tool set.
3. **Hybrid:** an embedding or keyword classifier for common intents (about 10 ms), with an LLM fallback for complex ones.

## Build plan (weekends, about 4–6 sessions)
1. **Text-only agent:** an LLM tool-calling loop with 3 mock tools (`get_policy_status`, `schedule_appointment`, `search_faq`). Mock data in SQLite.
2. **MCP:** move the tools into 1–2 MCP servers; the agent discovers tools at startup.
3. **RAG tool:** plug in the hybrid search + re-rank from the arxiv-paper-qa project for `search_faq`.
4. **Simple chat UI:** a web page (or Streamlit) with streaming responses and conversation history. *(Phase 2, optional: voice via browser mic → streaming STT → same agent → streaming TTS, with VAD and barge-in.)*
5. **Evals and observability:** a test set of about 50 utterances with expected tools; measure routing accuracy, task success, latency per stage (target under about 1 second to first audio) and cost.
6. **Guardrails:** identity check before personal data, PII redaction in logs, a "handoff to human" tool.
7. **README:** architecture diagram, demo GIF, latency and accuracy results, design trade-offs (cascaded vs. speech-to-speech).

## Tech choices (decide when starting)
- LLM with tool calling (Claude or another provider); the MCP Python SDK for tool servers.
- STT/TTS: a cloud streaming API, or local options (e.g. Whisper-based STT, an open-source TTS) to keep cost low.
- Python (FastAPI) backend; a simple web page for the mic; Docker; GitHub Actions for tests.
- Optional: an Azure OpenAI version, which doubles as Azure AI practice after AI-900.

## Tool registry design (how tools map to downstream systems)
- **Tools wrap downstream APIs.** The LLM only chooses the tool and its arguments; code makes the real call (REST/gRPC, a safe parameterized DB query, an adapter for legacy systems, or an async job and ticket). Keep tools **narrow and task-shaped** (`get_claim_status`), never generic (`run_sql`, `call_any_endpoint`).
- **Stage 1: config-driven registry (`tools.yaml`).** One entry per capability: name, description (when to use it and when not to), domain, owner, endpoint, auth, input JSON schema, permissions, `side_effects` (read_only | write | irreversible), timeout, version, enabled. At startup the agent builds (a) the tool list for the LLM and (b) the executor map, and it enforces permissions in code (verified caller; confirmation for writes). Generate most fields from **OpenAPI specs** when available.
- **Stage 2: MCP servers per domain.** Each domain team owns an MCP server that publishes its tools. The agent config lists servers, credentials and a per-agent **allow-list** (`policy.*`, `billing.get_*`), and tools are discovered at runtime.
- **Maintenance:**
  - every tool has an owner;
  - descriptions are reviewed like code;
  - tools are versioned (v2), with deprecation for breaking changes;
  - **routing evals in CI** (utterance → expected tools) gate every change;
  - observability per call (tool, redacted arguments, latency, errors, cost);
  - least-privilege credentials and rate limits.
- **Many tools:** route by domain first, or **retrieve tools dynamically** (embed the tool descriptions and pass the top 5–10 to the LLM, i.e. "RAG over tools").
- **Project plan:** start with `tools.yaml` (3–5 mock tools), then 1–2 MCP servers plus an agent-side `tools_policy.yaml` (permissions, allow-lists, side-effect rules), and add the routing eval set early.

## MCP (Model Context Protocol): primer and starter code
- **What it is:** an open standard (introduced by Anthropic in late 2024) for connecting AI apps to tools and data, "USB-C for AI tools". A system team builds one MCP server; any MCP client (your agent, Claude Desktop, Claude Code, IDEs) can use it.
- **Pieces:** host app (with the LLM) → MCP client → MCP servers (one per domain) → real systems. Protocol: JSON-RPC 2.0 (`initialize`, `tools/list`, `tools/call`). Transports: **stdio** (local subprocess; dev and desktop) or **Streamable HTTP** (web service; production).
- **Primitives:** **Tools** (actions the LLM calls), **Resources** (read-only context, e.g. `policy://P-1234`), **Prompts** (reusable templates).

**Server (Python SDK, `pip install "mcp[cli]"`), `policy_server.py`:**
```python
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("policy")
POLICIES = {"P-1234": {"status": "active", "premium": 142.50, "renews": "2027-01-01"}}

@mcp.tool()
def get_policy_status(policy_id: str) -> dict:
    """Look up an insurance policy's status, monthly premium, and renewal date.
    Use when the customer asks about their policy, bill amount, or renewal. Do NOT use for claims."""
    p = POLICIES.get(policy_id)
    return {"error": f"Policy {policy_id} not found"} if p is None else {"policy_id": policy_id, **p}

@mcp.tool()
def schedule_appointment(date: str, time: str, topic: str = "general") -> dict:
    """Book a call with a licensed agent. Date YYYY-MM-DD, time HH:MM (24h)."""
    return {"confirmed": True, "date": date, "time": time, "topic": topic}

@mcp.resource("policy://{policy_id}")
def policy_resource(policy_id: str) -> str:
    """Read-only policy details for context."""
    return str(POLICIES.get(policy_id, "not found"))

if __name__ == "__main__":
    mcp.run()  # stdio; or mcp.run(transport="streamable-http")
```
Function name = tool name; **docstring = description (routing logic)**; type hints = input schema.

**Test:** `mcp dev policy_server.py` (MCP Inspector UI) · **Use in Claude Code:** `claude mcp add policy -- python /path/to/policy_server.py`

**Client side in your agent:**
```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(command="python", args=["policy_server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()   # discover → convert to the LLM's tool format
            result = await session.call_tool("get_policy_status", {"policy_id": "P-1234"})
            print([t.name for t in tools.tools], result.content)

asyncio.run(main())
```
Agent loop: `list_tools()` on each server → convert to LLM tools → the LLM picks one → `call_tool()` on the right server → return the result to the LLM.

**Production tips:**
- Streamable HTTP in Docker/Kubernetes behind auth (OAuth or service tokens); never unauthenticated.
- One server per domain team; narrow tools; validate inputs and enforce permissions inside the server.
- Treat tool outputs as data, not instructions (prompt-injection risk).
- Logging, timeouts and rate limits, like any microservice.

## VAD (voice activity detection) options
- **Libraries (free, local):** Silero VAD (best default, PyTorch/ONNX), WebRTC VAD (`py-webrtcvad`, fast but less accurate), pyannote.audio (VAD plus diarization, heavier), `@ricky0123/vad-web` (Silero in the browser).
- **Built into streaming STT:** Deepgram endpointing, AssemblyAI end-of-turn, Google, Azure and AWS streaming STT, OpenAI Realtime "server VAD".
- **Frameworks (VAD and turn-taking included):** **Pipecat** (open source, Silero VAD; a good first choice), **LiveKit Agents** (WebRTC plus a turn-detection model), hosted Vapi or Retell.
- Plan: try Silero VAD in a 20-line mic script first, then build on Pipecat.

## Tips to remember
- Tool descriptions *are* the routing logic; say when to use each tool and when not to.
- Ask a clarifying question when a required parameter is missing; never guess personal data.
- Cap tool-call rounds (3–5); run independent tool calls in parallel.
- Enforce permissions in code, not just in the prompt.
- Write responses for speech: short sentences, numbers spoken naturally.

## Resume line (once built)
> Built an AI chat agent (voice-enabled in phase 2) with LLM tool-calling routing over MCP domain services and RAG (hybrid search + re-ranking), with routing evals and per-stage latency tracing (github.com/pxwang/mcp-agent-router).
