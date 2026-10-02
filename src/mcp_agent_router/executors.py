"""Tool implementations. Each function wraps a (mocked) downstream system call."""

import re

from mcp_agent_router.db import get_connection


def get_policy_status(policy_id: str) -> dict:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT policy_id, status, premium, renews FROM policies WHERE policy_id = ?",
            (policy_id,),
        ).fetchone()
    if row is None:
        return {"error": f"Policy {policy_id} not found"}
    return dict(row)


def schedule_appointment(date: str, time: str, topic: str = "general") -> dict:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO appointments (date, time, topic) VALUES (?, ?, ?)",
            (date, time, topic),
        )
        conn.commit()
    return {"confirmed": True, "date": date, "time": time, "topic": topic}


def search_faq(query: str, top_k: int = 2) -> dict:
    words = re.findall(r"[a-zA-Z]+", query.lower())
    terms = [w for w in words if len(w) > 2]
    with get_connection() as conn:
        rows = conn.execute("SELECT question, answer, keywords FROM faq_entries").fetchall()

    scored = []
    for row in rows:
        keywords = row["keywords"].lower()
        score = sum(1 for t in terms if t in keywords)
        if score > 0:
            scored.append((score, row))
    scored.sort(key=lambda s: s[0], reverse=True)

    matches = [{"question": r["question"], "answer": r["answer"]} for _, r in scored[:top_k]]
    if not matches:
        return {"matches": [], "note": "No FAQ entry matched; consider a human handoff."}
    return {"matches": matches}


EXECUTORS = {
    "get_policy_status": get_policy_status,
    "schedule_appointment": schedule_appointment,
    "search_faq": search_faq,
}
