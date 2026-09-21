from dataclasses import dataclass

import pytest
from jira import JIRAError

import pm_agent.tools.jira_tools as jira_tools
from pm_agent.tools.exceptions import JiraRateLimitedError


@dataclass
class FakeSettings:
    jira_api_token: str = "token"
    jira_base_url: str = "https://example.atlassian.net"


@dataclass
class FakeIssue:
    key: str


class FakeJira:
    keys = ["PROJ-1", "PROJ-2"]

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def create_issue(self, project, summary, description, issuetype, labels):
        return FakeIssue(self.keys.pop(0))


def _story(internal_id: str, title: str) -> dict:
    return {
        "internal_id": internal_id,
        "title": title,
        "description": f"Description for {title}",
        "acceptance_criteria": ["It works."],
        "story_points": 3,
        "priority": "must-have",
    }


def test_create_issues_batch_all_succeed(monkeypatch):
    FakeJira.keys = ["PROJ-1", "PROJ-2"]
    monkeypatch.setattr(jira_tools, "JIRA", FakeJira)
    monkeypatch.setattr(jira_tools, "load_settings", lambda: FakeSettings())
    monkeypatch.setattr(jira_tools.time, "sleep", lambda seconds: None)

    created, failures = jira_tools.create_issues_batch(
        "PROJ",
        [_story("story-001", "Create task"), _story("story-002", "Update task")],
        delay_seconds=0,
    )

    assert [story["jira_issue_key"] for story in created] == ["PROJ-1", "PROJ-2"]
    assert failures == []


def test_create_issues_batch_returns_partial_failures(monkeypatch):
    calls = {"count": 0}

    def fake_create_issue(project_key, summary, description, issue_type="Story", labels=None):
        calls["count"] += 1
        if calls["count"] == 2:
            raise RuntimeError("Jira exploded politely")
        return f"PROJ-{calls['count']}"

    monkeypatch.setattr(jira_tools, "create_issue", fake_create_issue)
    monkeypatch.setattr(jira_tools.time, "sleep", lambda seconds: None)

    created, failures = jira_tools.create_issues_batch(
        "PROJ",
        [
            _story("story-001", "Create task"),
            _story("story-002", "Update task"),
            _story("story-003", "Delete task"),
        ],
        delay_seconds=0,
    )

    assert [story["jira_issue_key"] for story in created] == ["PROJ-1", "PROJ-3"]
    assert len(failures) == 1
    assert failures[0]["story"]["internal_id"] == "story-002"


def test_create_issues_batch_retries_rate_limit(monkeypatch):
    calls = {"count": 0}

    def fake_create_issue(project_key, summary, description, issue_type="Story", labels=None):
        calls["count"] += 1
        if calls["count"] == 1:
            raise JiraRateLimitedError("rate limited")
        return "PROJ-1"

    monkeypatch.setattr(jira_tools, "create_issue", fake_create_issue)
    monkeypatch.setattr(jira_tools.time, "sleep", lambda seconds: None)

    created, failures = jira_tools.create_issues_batch(
        "PROJ",
        [_story("story-001", "Create task")],
        delay_seconds=0,
    )

    assert calls["count"] == 2
    assert created[0]["jira_issue_key"] == "PROJ-1"
    assert failures == []


def test_create_issue_maps_jira_429_to_rate_limited(monkeypatch):
    class RateLimitedJira:
        def __init__(self, **kwargs):
            pass

        def create_issue(self, project, summary, description, issuetype, labels):
            raise JIRAError(status_code=429, text="rate limited")

    monkeypatch.setattr(jira_tools, "JIRA", RateLimitedJira)
    monkeypatch.setattr(jira_tools, "load_settings", lambda: FakeSettings())

    with pytest.raises(JiraRateLimitedError):
        jira_tools.create_issue(
            project_key="PROJ",
            summary="Create task",
            description="Description",
        )
