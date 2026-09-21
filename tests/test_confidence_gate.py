import builtins

import pm_agent.tracking.confidence_gate as confidence_gate
from pm_agent.tracking.confidence_gate import apply_confidence_gate


def _story(status="in_progress"):
    return {
        "internal_id": "story-001",
        "jira_issue_key": "PROJ-1",
        "title": "Create task form",
        "description": "Allow users to create tasks.",
        "status": status,
        "assignee": "dev-1",
    }


def _state():
    return {
        "project_id": "project-123",
        "user_id": "dev-1",
        "conversation_history": [],
        "proposed_features": [],
        "scope_approved": True,
        "github_repo_url": None,
        "jira_project_key": "PROJ",
        "status_map": {
            "in_progress": {"transition_id": "21"},
            "review": {"transition_id": "31"},
            "done": {"transition_id": "41"},
        },
        "stories": [_story()],
        "story_embeddings": {},
        "needs_human_review": False,
        "phase": "tracking",
    }


def test_high_confidence_non_done_auto_transitions(monkeypatch):
    transitions = []
    monkeypatch.setattr(
        confidence_gate,
        "transition_issue",
        lambda issue_key, transition_id: transitions.append((issue_key, transition_id)),
    )
    state = _state()

    result, path, action = apply_confidence_gate(
        message="I started the task form",
        matched_story=state["stories"][0],
        score=0.99,
        target_status="in_progress",
        state=state,
    )

    assert transitions == [("PROJ-1", "21")]
    assert path == "auto_transition"
    assert action == "auto_transitioned_jira_issue"
    assert result["stories"][0]["status"] == "in_progress"


def test_medium_confidence_asks_for_confirmation(monkeypatch):
    transitions = []
    monkeypatch.setattr(builtins, "input", lambda prompt: "y")
    monkeypatch.setattr(
        confidence_gate,
        "transition_issue",
        lambda issue_key, transition_id: transitions.append((issue_key, transition_id)),
    )
    state = _state()

    result, path, action = apply_confidence_gate(
        message="task form update",
        matched_story=state["stories"][0],
        score=0.75,
        target_status="review",
        state=state,
    )

    assert transitions == [("PROJ-1", "31")]
    assert path == "confirm_story"
    assert action == "transitioned_after_story_confirmation"
    assert result["stories"][0]["status"] == "review"


def test_low_confidence_asks_which_story(capsys):
    state = _state()

    result, path, action = apply_confidence_gate(
        message="vague update",
        matched_story=state["stories"][0],
        score=0.50,
        target_status="in_progress",
        state=state,
    )

    captured = capsys.readouterr()
    assert "Which story is this about?" in captured.out
    assert result == state
    assert path == "ask_story_selection"
    assert action == "asked_developer_to_select_story"


def test_high_confidence_done_still_requires_confirmation(monkeypatch):
    transitions = []
    monkeypatch.setattr(builtins, "input", lambda prompt: "y")
    monkeypatch.setattr(
        confidence_gate,
        "transition_issue",
        lambda issue_key, transition_id: transitions.append((issue_key, transition_id)),
    )
    state = _state()

    result, path, action = apply_confidence_gate(
        message="task form is done",
        matched_story=state["stories"][0],
        score=0.99,
        target_status="done",
        state=state,
    )

    assert transitions == [("PROJ-1", "41")]
    assert path == "confirm_done"
    assert action == "transitioned_after_done_confirmation"
    assert result["stories"][0]["status"] == "done"
