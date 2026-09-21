"""Terminal loop for simulating developer tracking updates."""

from pm_agent.nodes.tracking import tracking_node
from pm_agent.state import PMAgentState


def _initial_state() -> PMAgentState:
    return {
        "project_id": "tracking-demo",
        "user_id": "dev-1",
        "conversation_history": [],
        "proposed_features": [],
        "scope_approved": True,
        "github_repo_url": "https://github.com/example/tracking-demo",
        "jira_project_key": "DEMO",
        "status_map": {
            "backlog": {"transition_id": "11", "transition_name": "Backlog"},
            "in_progress": {"transition_id": "21", "transition_name": "Start Progress"},
            "review": {"transition_id": "31", "transition_name": "Ready for Review"},
            "done": {"transition_id": "41", "transition_name": "Done"},
        },
        "stories": [
            {
                "internal_id": "story-001",
                "jira_issue_key": "DEMO-1",
                "title": "Create task capture form",
                "description": "Allow users to create tasks with title and description.",
                "status": "backlog",
                "assignee": "dev-1",
                "last_updated_by": None,
                "confidence": None,
            },
            {
                "internal_id": "story-002",
                "jira_issue_key": "DEMO-2",
                "title": "Build progress dashboard",
                "description": "Show counts for backlog, in progress, review, and done tasks.",
                "status": "in_progress",
                "assignee": "dev-1",
                "last_updated_by": None,
                "confidence": None,
            },
        ],
        "story_embeddings": {},
        "needs_human_review": False,
        "phase": "tracking",
    }


def main() -> None:
    state = _initial_state()
    print("Tracking CLI started. Press Ctrl+C or Ctrl+Z then Enter to exit.")

    while True:
        try:
            message = input("\nDeveloper update: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting tracking CLI.")
            return

        if not message:
            continue

        state["conversation_history"].append({"role": "user", "content": message})
        state = tracking_node(state)

        print("\nCurrent stories:")
        for story in state["stories"]:
            print(f"- {story['jira_issue_key']}: {story['status']} - {story['title']}")


if __name__ == "__main__":
    main()
