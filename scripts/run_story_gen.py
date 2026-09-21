"""Standalone runner for story generation."""

import json

from pm_agent.nodes.story_gen import story_gen_node
from pm_agent.state import PMAgentState


SAMPLE_FEATURES = [
    {
        "title": "Task capture",
        "description": "Users can quickly create and organize project tasks.",
        "priority": "high",
        "acceptance_criteria": [
            "A user can create a task with title and description.",
            "A user can assign a priority to a task.",
        ],
    },
    {
        "title": "Progress dashboard",
        "description": "Users can see project status and work distribution.",
        "priority": "medium",
        "acceptance_criteria": [
            "A user can view counts of open, in-progress, and done tasks."
        ],
    },
]


def _initial_state() -> PMAgentState:
    return {
        "project_id": "sample-story-generation",
        "user_id": "local-user",
        "conversation_history": [],
        "proposed_features": SAMPLE_FEATURES,
        "scope_approved": True,
        "github_repo_url": None,
        "jira_project_key": None,
        "status_map": {},
        "stories": [],
        "story_embeddings": {},
        "needs_human_review": False,
        "phase": "story_gen",
    }


def main() -> None:
    state = story_gen_node(_initial_state())
    attempts = state.get("story_gen_attempts", 0)

    print(f"Story generation attempts: {attempts}")
    print(f"Needs human review: {state['needs_human_review']}")
    print(json.dumps(state["stories"], indent=2))


if __name__ == "__main__":
    main()
