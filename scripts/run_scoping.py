"""Terminal runner for the scoping node only."""

import json

from pm_agent.nodes.scoping import scoping_node
from pm_agent.state import PMAgentState


def _initial_state() -> PMAgentState:
    return {
        "project_id": "local-scoping",
        "user_id": "local-user",
        "conversation_history": [],
        "proposed_features": [],
        "scope_approved": False,
        "github_repo_url": None,
        "jira_project_key": None,
        "status_map": {},
        "stories": [],
        "phase": "scoping",
    }


def main() -> None:
    state = _initial_state()
    print("Scoping CLI started. Press Ctrl+C or Ctrl+Z then Enter to exit.")

    while not state["scope_approved"]:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting scoping CLI.")
            return

        if not user_input:
            continue

        state["conversation_history"].append({"role": "user", "content": user_input})
        state = scoping_node(state)

        latest_message = state["conversation_history"][-1]
        print(f"\nAssistant: {latest_message['content']}")

    print("\nScope approved. Final feature list:")
    print(json.dumps(state["proposed_features"], indent=2))


if __name__ == "__main__":
    main()
