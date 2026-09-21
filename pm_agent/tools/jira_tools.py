"""Jira tool functions."""

import os
import time

from jira import JIRA, JIRAError

from pm_agent.config import load_settings
from pm_agent.tools.exceptions import (
    JiraIssueCreationError,
    JiraProjectProvisioningError,
    JiraRateLimitedError,
    JiraWorkflowInspectionError,
)


MAX_RATE_LIMIT_RETRIES = 3


def _get_jira_client() -> JIRA:
    settings = load_settings()
    jira_email = os.getenv("JIRA_EMAIL")

    if jira_email:
        return JIRA(
            server=settings.jira_base_url,
            basic_auth=(jira_email, settings.jira_api_token),
        )

    return JIRA(
        server=settings.jira_base_url,
        token_auth=settings.jira_api_token,
    )


def create_project(key: str, name: str) -> str:
    """Create a Jira project and return its project key."""

    jira = _get_jira_client()

    try:
        project = jira.create_project(key=key, name=name)
    except JIRAError as exc:
        raise JiraProjectProvisioningError(
            f"Failed to create Jira project '{key}' at configured Jira site."
        ) from exc

    if isinstance(project, dict):
        return str(project.get("key", key))

    return str(getattr(project, "key", key))


def create_issue(
    project_key: str,
    summary: str,
    description: str,
    issue_type: str = "Story",
    labels: list[str] | None = None,
) -> str:
    """Create a Jira issue and return the Jira-generated issue key."""

    jira = _get_jira_client()

    try:
        issue = jira.create_issue(
            project=project_key,
            summary=summary,
            description=description,
            issuetype={"name": issue_type},
            labels=labels or [],
        )
    except JIRAError as exc:
        if _jira_status_code(exc) == 429:
            raise JiraRateLimitedError("Jira rate limit reached while creating issue.") from exc
        raise JiraIssueCreationError(
            f"Failed to create Jira issue '{summary}' in project '{project_key}'."
        ) from exc

    return str(getattr(issue, "key"))


def create_issues_batch(
    project_key: str,
    stories: list[dict],
    delay_seconds: float = 0.5,
) -> tuple[list[dict], list[dict]]:
    """Create Jira issues sequentially and return successes plus failures."""

    created_stories = []
    failures = []

    for story in stories:
        try:
            jira_issue_key = _create_issue_with_rate_limit_retry(
                project_key=project_key,
                story=story,
            )
        except Exception as exc:
            failures.append(
                {
                    "story": story,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                }
            )
        else:
            created_stories.append({**story, "jira_issue_key": jira_issue_key})

        time.sleep(delay_seconds)

    return created_stories, failures


def transition_issue(issue_key: str, transition_id: str) -> None:
    """Move a Jira issue using a project-specific transition ID."""

    jira = _get_jira_client()

    try:
        jira.transition_issue(issue_key, transition_id)
    except JIRAError as exc:
        if _jira_status_code(exc) == 429:
            raise JiraRateLimitedError(
                f"Jira rate limit reached while transitioning issue '{issue_key}'."
            ) from exc
        raise JiraIssueCreationError(
            f"Failed to transition Jira issue '{issue_key}' with transition '{transition_id}'."
        ) from exc


def _create_issue_with_rate_limit_retry(project_key: str, story: dict) -> str:
    delay = 1.0

    for attempt in range(1, MAX_RATE_LIMIT_RETRIES + 1):
        try:
            return create_issue(
                project_key=project_key,
                summary=story["title"],
                description=_format_story_description(story),
                issue_type="Story",
                labels=["pm-agent"],
            )
        except JiraRateLimitedError:
            if attempt == MAX_RATE_LIMIT_RETRIES:
                raise
            time.sleep(delay)
            delay *= 2

    raise JiraRateLimitedError("Jira rate limit retry loop exited unexpectedly.")


def _format_story_description(story: dict) -> str:
    criteria = story.get("acceptance_criteria", [])
    criteria_text = "\n".join(f"- {item}" for item in criteria)
    return (
        f"{story['description']}\n\n"
        f"Acceptance criteria:\n{criteria_text}\n\n"
        f"Story points: {story['story_points']}\n"
        f"Priority: {story['priority']}\n"
        f"Internal ID: {story['internal_id']}"
    )


def get_workflow_transitions(project_key: str) -> dict:
    """Fetch available workflow transitions for a project at runtime."""

    jira = _get_jira_client()
    probe_issue = None
    created_probe_issue = False

    try:
        existing_issues = jira.search_issues(
            f'project = "{project_key}" ORDER BY created ASC',
            maxResults=1,
        )

        if existing_issues:
            probe_issue = existing_issues[0]
        else:
            probe_issue = jira.create_issue(
                project=project_key,
                summary="Workflow transition inspection probe",
                description="Temporary issue created by pm_agent to inspect workflow transitions.",
                issuetype={"name": "Task"},
            )
            created_probe_issue = True

        transitions = jira.transitions(probe_issue)
    except JIRAError as exc:
        raise JiraWorkflowInspectionError(
            f"Failed to inspect Jira workflow transitions for project '{project_key}'."
        ) from exc
    finally:
        if created_probe_issue and probe_issue is not None:
            try:
                probe_issue.delete()
            except JIRAError:
                pass

    return {
        str(transition["name"]): {
            "id": str(transition["id"]),
            "name": str(transition["name"]),
            "to_status": _transition_to_status(transition),
        }
        for transition in transitions
    }


def _transition_to_status(transition: dict) -> str | None:
    to_status = transition.get("to")
    if not to_status:
        return None
    if isinstance(to_status, dict):
        name = to_status.get("name")
        return str(name) if name is not None else None
    name = getattr(to_status, "name", None)
    return str(name) if name is not None else None


def _jira_status_code(exc: JIRAError) -> int | None:
    status_code = getattr(exc, "status_code", None)
    if status_code is not None:
        return int(status_code)

    response = getattr(exc, "response", None)
    response_status = getattr(response, "status_code", None)
    return int(response_status) if response_status is not None else None
