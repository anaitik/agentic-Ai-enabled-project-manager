from dataclasses import dataclass

import pytest

import pm_agent.tools.jira_tools as jira_tools
import pm_agent.tools.status_mapping as status_mapping
from pm_agent.tools.exceptions import StatusMappingError


@dataclass
class FakeSettings:
    jira_api_token: str = "token"
    jira_base_url: str = "https://example.atlassian.net"


@dataclass
class FakeProject:
    key: str


class FakeIssue:
    def __init__(self):
        self.deleted = False

    def delete(self):
        self.deleted = True


class FakeJira:
    project = FakeProject("DEMO")
    existing_issues = [FakeIssue()]
    transitions_result = [
        {"id": "11", "name": "Backlog", "to": {"name": "Backlog"}},
        {"id": "21", "name": "Start Progress", "to": {"name": "In Progress"}},
        {"id": "31", "name": "Ready for Review", "to": {"name": "Review"}},
        {"id": "41", "name": "Done", "to": {"name": "Done"}},
    ]

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def create_project(self, key, name):
        return self.project

    def search_issues(self, jql, maxResults):
        return self.existing_issues

    def create_issue(self, project, summary, description, issuetype):
        return FakeIssue()

    def transitions(self, issue):
        return self.transitions_result


def test_create_project_success(monkeypatch):
    monkeypatch.setattr(jira_tools, "JIRA", FakeJira)
    monkeypatch.setattr(jira_tools, "load_settings", lambda: FakeSettings())

    assert jira_tools.create_project("DEMO", "Demo Project") == "DEMO"


def test_get_workflow_transitions_returns_mapping(monkeypatch):
    monkeypatch.setattr(jira_tools, "JIRA", FakeJira)
    monkeypatch.setattr(jira_tools, "load_settings", lambda: FakeSettings())

    transitions = jira_tools.get_workflow_transitions("DEMO")

    assert transitions["Start Progress"] == {
        "id": "21",
        "name": "Start Progress",
        "to_status": "In Progress",
    }


def test_build_status_map_success(monkeypatch):
    monkeypatch.setattr(
        status_mapping,
        "get_workflow_transitions",
        lambda project_key: {
            "Backlog": {"id": "11", "name": "Backlog", "to_status": "Backlog"},
            "Start Progress": {
                "id": "21",
                "name": "Start Progress",
                "to_status": "In Progress",
            },
            "Ready for Review": {
                "id": "31",
                "name": "Ready for Review",
                "to_status": "Review",
            },
            "Done": {"id": "41", "name": "Done", "to_status": "Done"},
        },
    )

    result = status_mapping.build_status_map("DEMO")

    assert result["in_progress"]["transition_id"] == "21"
    assert result["review"]["transition_name"] == "Ready for Review"


def test_build_status_map_raises_when_transition_missing(monkeypatch):
    monkeypatch.setattr(
        status_mapping,
        "get_workflow_transitions",
        lambda project_key: {
            "Backlog": {"id": "11", "name": "Backlog", "to_status": "Backlog"},
            "Start Progress": {
                "id": "21",
                "name": "Start Progress",
                "to_status": "In Progress",
            },
            "Done": {"id": "41", "name": "Done", "to_status": "Done"},
        },
    )

    with pytest.raises(StatusMappingError, match="review"):
        status_mapping.build_status_map("DEMO")
