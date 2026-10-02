"""Interactive text chat REPL for the agent."""

import sys

from mcp_agent_router.agent import Agent


def main() -> None:
    agent = Agent()
    print("mcp-agent-router (type 'exit' to quit)")
    while True:
        try:
            user_text = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_text:
            continue
        if user_text.lower() in {"exit", "quit"}:
            break

        reply = agent.send(user_text)
        print(f"agent> {reply}")


if __name__ == "__main__":
    sys.exit(main())
