"""Per-call audit trail for tool routing: raw query, resolved tool, latency, outcome."""

import json
from datetime import datetime, timezone

from mcp_agent_router.db import get_connection


def log_tool_call(
    query: str,
    tool_name: str,
    arguments: dict,
    latency_ms: float,
    success: bool,
    error: str | None = None,
) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO tool_call_logs (ts, query, tool_name, arguments, latency_ms, success, error) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                datetime.now(timezone.utc).isoformat(),
                query,
                tool_name,
                json.dumps(arguments),
                latency_ms,
                int(success),
                error,
            ),
        )
        conn.commit()


def recent_tool_calls(limit: int = 20) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT ts, query, tool_name, arguments, latency_ms, success, error "
            "FROM tool_call_logs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
