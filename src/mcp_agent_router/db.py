"""SQLite-backed mock data for the domain tools (policies, appointments, FAQ)."""

import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.environ.get("MCP_AGENT_ROUTER_DB", os.path.join(os.path.dirname(__file__), "..", "..", "data", "mock.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS policies (
    policy_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    premium REAL NOT NULL,
    renews TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    topic TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS faq_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    keywords TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tool_call_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    query TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    arguments TEXT NOT NULL,
    latency_ms REAL NOT NULL,
    success INTEGER NOT NULL,
    error TEXT
);
"""

SEED_POLICIES = [
    ("P-1234", "active", 142.50, "2027-01-01"),
    ("P-5678", "lapsed", 98.00, "2026-06-15"),
    ("P-9999", "active", 210.75, "2027-03-20"),
]

SEED_FAQ = [
    (
        "What does comprehensive coverage include?",
        "Comprehensive coverage pays for damage to your car from non-collision events: theft, fire, "
        "vandalism, weather, and hitting an animal.",
        "comprehensive coverage include damage theft fire vandalism weather animal",
    ),
    (
        "How do I change my billing date?",
        "You can change your monthly billing date in the account portal under Billing > Payment Schedule, "
        "or by asking an agent to update it for you.",
        "change billing date payment schedule account portal",
    ),
    (
        "What is a deductible?",
        "A deductible is the amount you pay out of pocket on a claim before your insurance coverage pays "
        "the rest.",
        "deductible claim out of pocket pay",
    ),
    (
        "How do I file a claim?",
        "File a claim online in the app under Claims > New Claim, or call the claims hotline. Have your "
        "policy number and incident details ready.",
        "file claim new claim hotline policy number incident",
    ),
]


def _seed_if_empty(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM policies").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO policies (policy_id, status, premium, renews) VALUES (?, ?, ?, ?)",
            SEED_POLICIES,
        )
    if conn.execute("SELECT COUNT(*) FROM faq_entries").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO faq_entries (question, answer, keywords) VALUES (?, ?, ?)",
            SEED_FAQ,
        )
    conn.commit()


@contextmanager
def get_connection():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)
        _seed_if_empty(conn)
        yield conn
    finally:
        conn.close()
