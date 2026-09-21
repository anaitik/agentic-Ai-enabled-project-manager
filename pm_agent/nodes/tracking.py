"""Chat-based developer tracking node."""

from pm_agent.state import PMAgentState
from pm_agent.tracking.confidence_gate import apply_confidence_gate
from pm_agent.tracking.event_logger import log_match_attempt
from pm_agent.tracking.intent_classifier import classify_intent
from pm_agent.tracking.story_matcher import match_story


def _latest_user_message(state: PMAgentState) -> str | None:
    for message in reversed(state["conversation_history"]):
        if message.get("role") == "user":
            return str(message.get("content", "")).strip()
    return None


def _target_status_from_message(message: str) -> str:
    normalized = message.lower()
    if any(word in normalized for word in ["done", "complete", "completed", "finished", "closed"]):
        return "done"
    if any(word in normalized for word in ["review", "pr", "pull request"]):
        return "review"
    if any(word in normalized for word in ["started", "working", "progress", "implementing"]):
        return "in_progress"
    return "in_progress"


def tracking_node(state: PMAgentState) -> PMAgentState:
    """Process the latest developer chat update."""

    message = _latest_user_message(state)
    if not message:
        return state

    intent = classify_intent(message)
    if intent != "status_update":
        log_match_attempt(
            message=message,
            matched_story_key=None,
            score=0.0,
            chosen_path=f"intent_{intent}",
            final_action="no_transition",
        )
        return {**state, "phase": "tracking"}

    matched_story, score = match_story(
        message=message,
        developer_id=state["user_id"],
        state=state,
    )
    target_status = _target_status_from_message(message)

    updated_state, chosen_path, final_action = apply_confidence_gate(
        message=message,
        matched_story=matched_story,
        score=score,
        target_status=target_status,
        state=state,
    )
    log_match_attempt(
        message=message,
        matched_story_key=matched_story.get("jira_issue_key") if matched_story else None,
        score=score,
        chosen_path=chosen_path,
        final_action=final_action,
    )

    return updated_state
