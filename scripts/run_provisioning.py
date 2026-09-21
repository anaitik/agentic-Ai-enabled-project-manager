"""Standalone runner for the provisioning node."""

import json

from pm_agent.nodes.provisioning import (
    provisioning_node,
    slugify_jira_project_key,
    slugify_repo_name,
)
from pm_agent.state import PMAgentState


def _initial_state(project_id: str) -> PMAgentState:
    return {
        "project_id": project_id,
        "user_id": "local-user",
        "conversation_history": [],
        "proposed_features": [],
        "scope_approved": True,
        "github_repo_url": None,
        "jira_project_key": None,
        "status_map": {},
        "stories": [],
        "needs_human_review": False,
        "phase": "provisioning",
    }


def main() -> None:
    project_id = input("Project name/id for throwaway repo: ").strip()
    if not project_id:
        print("Project name/id is required.")
        return

    repo_name = slugify_repo_name(project_id)
    jira_key = slugify_jira_project_key(project_id)
    print(f"Creating private GitHub repo: {repo_name}")
    print(f"Creating Jira project: {jira_key}")

    state = provisioning_node(_initial_state(project_id))
    print(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
