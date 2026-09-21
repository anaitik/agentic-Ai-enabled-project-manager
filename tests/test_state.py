from typing import get_args

from pm_agent.state import PMAgentState


def test_pm_agent_state_accepts_dummy_values():
    state: PMAgentState = {
        "project_id": "project-123",
        "user_id": "user-456",
        "conversation_history": [{"role": "user", "content": "Build a project manager."}],
        "proposed_features": [{"title": "Issue tracking", "priority": "high"}],
        "scope_approved": False,
        "github_repo_url": None,
        "jira_project_key": None,
        "status_map": {},
        "stories": [
            {
                "internal_id": "story-1",
                "jira_issue_key": None,
                "title": "Create project skeleton",
                "description": "Set up the initial package, graph, and tests.",
                "status": "draft",
                "assignee": None,
                "last_updated_by": "user-456",
                "confidence": 0.95,
            }
        ],
        "phase": "scoping",
    }

    assert set(state) == set(PMAgentState.__annotations__)
    assert state["phase"] in get_args(PMAgentState.__annotations__["phase"])
    assert isinstance(state["conversation_history"], list)
    assert isinstance(state["proposed_features"], list)
    assert isinstance(state["stories"], list)
