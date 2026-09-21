import pm_agent.tracking.story_matcher as story_matcher
from pm_agent.tracking.story_matcher import match_story


def _state():
    return {
        "project_id": "project-123",
        "user_id": "dev-1",
        "conversation_history": [],
        "proposed_features": [],
        "scope_approved": True,
        "github_repo_url": None,
        "jira_project_key": "PROJ",
        "status_map": {},
        "stories": [
            {
                "internal_id": "story-001",
                "jira_issue_key": "PROJ-1",
                "title": "Create task form",
                "description": "Allow users to create tasks.",
                "status": "in_progress",
                "assignee": "dev-1",
            },
            {
                "internal_id": "story-002",
                "jira_issue_key": "PROJ-2",
                "title": "Build billing page",
                "description": "Allow users to pay invoices.",
                "status": "in_progress",
                "assignee": "dev-2",
            },
            {
                "internal_id": "story-003",
                "jira_issue_key": "PROJ-3",
                "title": "Archive completed task",
                "description": "Archive completed tasks.",
                "status": "done",
                "assignee": "dev-1",
            },
        ],
        "story_embeddings": {},
        "needs_human_review": False,
        "phase": "tracking",
    }


def test_match_story_filters_to_developer_non_done_stories(monkeypatch):
    embeddings = {
        "task update": [1.0, 0.0],
        "Create task form\nAllow users to create tasks.": [1.0, 0.0],
    }
    calls = []

    def fake_embed(text):
        calls.append(text)
        return embeddings[text]

    monkeypatch.setattr(story_matcher, "_embed_text", fake_embed)

    state = _state()
    story, score = match_story("task update", "dev-1", state)

    assert story["jira_issue_key"] == "PROJ-1"
    assert score == 1.0
    assert "Build billing page\nAllow users to pay invoices." not in calls
    assert "Archive completed task\nArchive completed tasks." not in calls


def test_match_story_caches_story_embeddings(monkeypatch):
    embeddings = {
        "task update": [1.0, 0.0],
        "another task update": [1.0, 0.0],
        "Create task form\nAllow users to create tasks.": [1.0, 0.0],
    }
    calls = []

    def fake_embed(text):
        calls.append(text)
        return embeddings[text]

    monkeypatch.setattr(story_matcher, "_embed_text", fake_embed)

    state = _state()
    match_story("task update", "dev-1", state)
    match_story("another task update", "dev-1", state)

    assert calls.count("Create task form\nAllow users to create tasks.") == 1
