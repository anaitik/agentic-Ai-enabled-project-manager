"""Push validated stories to Jira after human approval."""

from pm_agent.state import PMAgentState
from pm_agent.tools.approval import request_approval
from pm_agent.tools.jira_tools import create_issues_batch


def push_stories_node(state: PMAgentState) -> PMAgentState:
    """Ask for approval, create Jira issues, and write Jira keys into state."""

    stories_without_jira_keys = [
        story for story in state["stories"] if not story.get("jira_issue_key")
    ]
    if not stories_without_jira_keys:
        return {**state, "phase": "push_stories"}

    assert all(
        "jira_issue_key" not in story or not story["jira_issue_key"]
        for story in stories_without_jira_keys
    ), "jira_issue_key must come only from Jira API responses, never from the LLM."

    if not request_approval(stories_without_jira_keys):
        return {
            **state,
            "needs_human_review": True,
            "phase": "push_stories",
            "jira_push_failures": [],
        }

    created_stories, failures = create_issues_batch(
        project_key=state["jira_project_key"],
        stories=stories_without_jira_keys,
    )
    created_by_internal_id = {
        story["internal_id"]: story for story in created_stories
    }
    updated_stories = [
        created_by_internal_id.get(story.get("internal_id"), story)
        for story in state["stories"]
    ]

    return {
        **state,
        "stories": updated_stories,
        "needs_human_review": bool(failures),
        "phase": "push_stories",
        "jira_push_failures": failures,
    }
