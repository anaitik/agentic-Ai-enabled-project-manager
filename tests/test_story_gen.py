from dataclasses import dataclass

import pm_agent.nodes.story_gen as story_gen_module
from pm_agent.nodes.story_gen import story_gen_node
from pm_agent.state import PMAgentState


@dataclass
class FakeResponse:
    content: str


class FakeLLM:
    def __init__(self, responses: list[str]):
        self.responses = responses
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        return FakeResponse(self.responses.pop(0))


def _state() -> PMAgentState:
    return {
        "project_id": "project-123",
        "user_id": "user-456",
        "conversation_history": [],
        "proposed_features": [{"title": "Task capture", "description": "Create tasks"}],
        "scope_approved": True,
        "github_repo_url": "https://github.com/test-owner/project-123",
        "jira_project_key": "PROJ",
        "status_map": {},
        "stories": [],
        "needs_human_review": False,
        "phase": "story_gen",
    }


VALID_RESPONSE = """{
  "stories": [
    {
      "internal_id": "story-001",
      "title": "Create task",
      "description": "Allow users to create a task.",
      "acceptance_criteria": ["A user can create a task."],
      "story_points": 3,
      "priority": "must-have"
    }
  ]
}"""


def test_story_gen_retries_invalid_stories_and_succeeds(monkeypatch):
    fake_llm = FakeLLM(
        [
            """{"stories": [{"internal_id": "story-001", "title": "Bad", "description": "", "acceptance_criteria": [], "story_points": 4, "priority": "must-have"}]}""",
            VALID_RESPONSE,
        ]
    )
    monkeypatch.setattr(story_gen_module, "get_llm", lambda: fake_llm)

    result = story_gen_node(_state())

    assert len(fake_llm.calls) == 2
    assert "fix_these_issues" in fake_llm.calls[1][1]["content"]
    assert result["needs_human_review"] is False
    assert result["story_gen_attempts"] == 2
    assert result["stories"][0]["internal_id"] == "story-001"


def test_story_gen_sets_human_review_after_three_failures(monkeypatch):
    fake_llm = FakeLLM(
        [
            """{"stories": [{"internal_id": "story-001", "title": "Bad", "description": "", "acceptance_criteria": [], "story_points": 4, "priority": "must-have"}]}""",
            """{"stories": [{"internal_id": "story-001", "title": "Bad", "description": "", "acceptance_criteria": [], "story_points": 4, "priority": "must-have"}]}""",
            """{"stories": [{"internal_id": "story-001", "title": "Bad", "description": "", "acceptance_criteria": [], "story_points": 4, "priority": "must-have"}]}""",
        ]
    )
    monkeypatch.setattr(story_gen_module, "get_llm", lambda: fake_llm)

    result = story_gen_node(_state())

    assert len(fake_llm.calls) == 3
    assert result["needs_human_review"] is True
    assert result["story_gen_attempts"] == 3
    assert result["stories"] == []
