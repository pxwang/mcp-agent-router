"""Routing eval runner: replays evals/routing_evals.jsonl through the agent and
checks whether each utterance triggered the expected tool(s).

Calls the Anthropic API once per case - run manually, not wired into CI or any
pre-commit/pre-push hook, to avoid unnecessary API cost on every check-in:

    python evals/run_routing_evals.py
"""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from mcp_agent_router.agent import Agent

EVALS_PATH = Path(__file__).resolve().parent / "routing_evals.jsonl"


def load_cases(path: Path = EVALS_PATH) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def tools_called(agent: Agent) -> set[str]:
    names = set()
    for message in agent.messages:
        if message["role"] != "assistant":
            continue
        for block in message["content"]:
            if getattr(block, "type", None) == "tool_use":
                names.add(block.name)
    return names


def run() -> int:
    load_dotenv()
    cases = load_cases()
    passed = 0

    for case in cases:
        agent = Agent()
        agent.send(case["utterance"])
        actual = tools_called(agent)
        expected = set(case["expected_tools"])
        ok = actual == expected
        passed += ok

        print(f"[{'PASS' if ok else 'FAIL'}] {case['utterance']!r}")
        print(f"       expected={sorted(expected)} actual={sorted(actual)}")

    total = len(cases)
    print(f"\n{passed}/{total} passed ({passed / total:.0%})")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run())
