"""Story generation node with deterministic validation and retry."""

import json

from pm_agent.llm import get_llm
from pm_agent.prompts.story_gen_prompt import STORY_GEN_SYSTEM_PROMPT
from pm_agent.state import PMAgentState
from pm_agent.tools.approval import request_approval
from pm_agent.tools.jira_tools import create_issues_batch
from pm_agent.validation.story_validator import validate_stories


MAX_STORY_GEN_ATTEMPTS = 3


def _response_content(response: object) -> str:
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content
    return str(content)


def _build_messages(state: PMAgentState, errors: list[str] | None = None) -> list[dict]:
    user_content = {
        "approved_features": state["proposed_features"],
        "required_output_schema": {
            "stories": [
                {
                    "internal_id": "str",
                    "title": "str",
                    "description": "str",
                    "acceptance_criteria": ["str"],
                    "story_points": "int",
                    "priority": "must-have|nice-to-have",
                }
            ]
        },
    }

    if errors:
        user_content["fix_these_issues"] = errors

    return [
        {"role": "system", "content": STORY_GEN_SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(user_content, indent=2)},
    ]


def _parse_stories(response_text: str) -> tuple[list[dict], list[str]]:
    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError as exc:
        return [], [f"Response must be valid JSON only: {exc.msg}."]

    stories = parsed.get("stories")
    if not isinstance(stories, list):
        return [], ["Response JSON must contain a 'stories' list."]

    return stories, []


def story_gen_node(state: PMAgentState) -> PMAgentState:
    """Generate stories from approved features and retry invalid outputs."""

    llm = get_llm()
    errors: list[str] | None = None

    for attempt in range(1, MAX_STORY_GEN_ATTEMPTS + 1):
        response = llm.invoke(_build_messages(state, errors))
        response_text = _response_content(response)

        stories, parse_errors = _parse_stories(response_text)
        if parse_errors:
            errors = parse_errors
            continue

        is_valid, validation_errors = validate_stories(stories)
        if is_valid:
            assert all(
                "jira_issue_key" not in story for story in stories
            ), "jira_issue_key must come only from Jira API responses, never from the LLM."

            if not request_approval(stories):
                return {
                    **state,
                    "stories": stories,
                    "needs_human_review": True,
                    "phase": "story_gen",
                    "story_gen_attempts": attempt,
                    "jira_push_failures": [],
                }

            created_stories, failures = create_issues_batch(
                project_key=state["jira_project_key"],
                stories=stories,
            )

            return {
                **state,
                "stories": created_stories,
                "needs_human_review": bool(failures),
                "phase": "story_gen",
                "story_gen_attempts": attempt,
                "jira_push_failures": failures,
            }

        errors = validation_errors

    return {
        **state,
        "needs_human_review": True,
        "phase": "story_gen",
        "story_gen_attempts": MAX_STORY_GEN_ATTEMPTS,
    }
