from dataclasses import dataclass

import pm_agent.nodes.scoping as scoping_module
from pm_agent.nodes.scoping import scoping_node
from pm_agent.state import PMAgentState


@dataclass
class FakeResponse:
    content: str


class FakeLLM:
    def __init__(self, content: str):
        self.content = content
        self.messages = None

    def invoke(self, messages):
        self.messages = messages
        return FakeResponse(self.content)


def _state() -> PMAgentState:
    return {
        "project_id": "project-123",
        "user_id": "user-456",
        "conversation_history": [{"role": "user", "content": "I want a task manager."}],
        "proposed_features": [{"title": "Existing feature"}],
        "scope_approved": False,
        "github_repo_url": None,
        "jira_project_key": None,
        "status_map": {},
        "stories": [],
        "phase": "scoping",
    }


def test_scoping_response_without_feature_list_leaves_scope_fields_unchanged(monkeypatch):
    fake_llm = FakeLLM("Who are the primary users for this task manager?")
    monkeypatch.setattr(scoping_module, "get_llm", lambda: fake_llm)

    state = _state()
    result = scoping_node(state)

    assert result["proposed_features"] == state["proposed_features"]
    assert result["scope_approved"] is state["scope_approved"]
    assert result["conversation_history"][-1] == {
        "role": "assistant",
        "content": "Who are the primary users for this task manager?",
    }


def test_scoping_response_with_valid_feature_list_updates_scope_fields(monkeypatch):
    fake_llm = FakeLLM(
        """Approved scope:
<feature_list>
{
  "features": [
    {
      "title": "Task capture",
      "description": "Users can quickly create tasks.",
      "priority": "high",
      "acceptance_criteria": ["A user can create a task with a title."]
    }
  ],
  "scope_approved": true
}
</feature_list>"""
    )
    monkeypatch.setattr(scoping_module, "get_llm", lambda: fake_llm)

    result = scoping_node(_state())

    assert result["proposed_features"] == [
        {
            "title": "Task capture",
            "description": "Users can quickly create tasks.",
            "priority": "high",
            "acceptance_criteria": ["A user can create a task with a title."],
        }
    ]
    assert result["scope_approved"] is True
