"""Confidence gating for tracking story updates."""

from pm_agent.state import PMAgentState
from pm_agent.tools.jira_tools import transition_issue


AUTO_TRANSITION_THRESHOLD = 0.85
CONFIRM_THRESHOLD = 0.60


def apply_confidence_gate(
    message: str,
    matched_story: dict | None,
    score: float,
    target_status: str,
    state: PMAgentState,
) -> tuple[PMAgentState, str, str]:
    """Choose the tracking action based on score and target status."""

    if matched_story is None or score <= CONFIRM_THRESHOLD:
        _print_open_stories(state)
        return state, "ask_story_selection", "asked_developer_to_select_story"

    if target_status == "done":
        if _confirm(
            f"Confirm closing {matched_story.get('jira_issue_key')} "
            f"'{matched_story.get('title')}' as done? [y/n]: "
        ):
            return _transition_and_update(state, matched_story, target_status), (
                "confirm_done"
            ), "transitioned_after_done_confirmation"
        return state, "confirm_done", "developer_declined_done_transition"

    if score > AUTO_TRANSITION_THRESHOLD:
        return (
            _transition_and_update(state, matched_story, target_status),
            "auto_transition",
            "auto_transitioned_jira_issue",
        )

    if _confirm(
        f"Did you mean {matched_story.get('jira_issue_key')} "
        f"'{matched_story.get('title')}'? [y/n]: "
    ):
        return (
            _transition_and_update(state, matched_story, target_status),
            "confirm_story",
            "transitioned_after_story_confirmation",
        )

    _print_open_stories(state)
    return state, "confirm_story", "developer_declined_match"


def _transition_and_update(
    state: PMAgentState,
    matched_story: dict,
    target_status: str,
) -> PMAgentState:
    jira_issue_key = matched_story.get("jira_issue_key")
    transition_id = state["status_map"][target_status]["transition_id"]
    transition_issue(jira_issue_key, transition_id)

    updated_stories = []
    for story in state["stories"]:
        if story is matched_story or story.get("internal_id") == matched_story.get("internal_id"):
            updated_stories.append(
                {
                    **story,
                    "status": target_status,
                    "last_updated_by": state["user_id"],
                }
            )
        else:
            updated_stories.append(story)

    return {
        **state,
        "stories": updated_stories,
        "phase": "tracking",
    }


def _confirm(prompt: str) -> bool:
    while True:
        answer = input(prompt).strip().lower()
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Please answer y or n.")


def _print_open_stories(state: PMAgentState) -> None:
    developer_id = state["user_id"]
    open_stories = [
        story
        for story in state["stories"]
        if story.get("assignee") == developer_id and story.get("status") != "done"
    ]
    print("\nWhich story is this about?")
    for story in open_stories:
        print(f"- {story.get('jira_issue_key')}: {story.get('title')}")
