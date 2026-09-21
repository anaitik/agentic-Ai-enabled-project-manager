"""Map internal pm_agent statuses to project-specific Jira transitions."""

import re

from pm_agent.tools.exceptions import StatusMappingError
from pm_agent.tools.jira_tools import get_workflow_transitions


INTERNAL_STATUSES = ["backlog", "in_progress", "review", "done"]

STATUS_ALIASES = {
    "backlog": ["backlog", "to do", "todo", "open", "selected for development"],
    "in_progress": ["in progress", "start progress", "doing", "started"],
    "review": ["review", "in review", "code review", "ready for review"],
    "done": ["done", "complete", "completed", "close issue", "closed", "resolve issue"],
}


def build_status_map(project_key: str) -> dict:
    """Build and validate the project-specific Jira status transition map."""

    transitions = get_workflow_transitions(project_key)
    status_map = {}

    for internal_status in INTERNAL_STATUSES:
        match = _find_transition_match(
            aliases=STATUS_ALIASES[internal_status],
            transitions=transitions,
        )
        if match is None:
            found = _format_found_transitions(transitions)
            expected = ", ".join(STATUS_ALIASES[internal_status])
            raise StatusMappingError(
                "Could not map internal status "
                f"'{internal_status}' for Jira project '{project_key}'. "
                f"Expected a transition/status matching one of: {expected}. "
                f"Found transitions: {found}."
            )

        status_map[internal_status] = {
            "transition_id": match["id"],
            "transition_name": match["name"],
            "jira_status": match["to_status"],
        }

    return status_map


def _find_transition_match(aliases: list[str], transitions: dict) -> dict | None:
    normalized_aliases = {_normalize(alias) for alias in aliases}

    for transition in transitions.values():
        names_to_check = [
            transition.get("name"),
            transition.get("to_status"),
        ]
        for name in names_to_check:
            if name and _normalize(name) in normalized_aliases:
                return transition

    return None


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _format_found_transitions(transitions: dict) -> str:
    if not transitions:
        return "none"

    return ", ".join(
        f"{transition['name']} (id={transition['id']}, to={transition['to_status']})"
        for transition in transitions.values()
    )

