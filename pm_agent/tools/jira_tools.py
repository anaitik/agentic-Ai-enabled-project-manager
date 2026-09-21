"""Jira tool functions."""

import os

from jira import JIRA, JIRAError

from pm_agent.config import load_settings
from pm_agent.tools.exceptions import (
    JiraProjectProvisioningError,
    JiraWorkflowInspectionError,
)


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

