"""Provisioning node for creating external project resources."""

import re

from pm_agent.state import PMAgentState
from pm_agent.tools.github_tools import create_repo
from pm_agent.tools.jira_tools import create_project
from pm_agent.tools.status_mapping import build_status_map


def slugify_repo_name(value: str) -> str:
    """Convert project text into a GitHub-friendly repository name."""

    slug = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "pm-agent-project"


def slugify_jira_project_key(value: str) -> str:
    """Convert project text into a Jira-compatible project key."""

    key = re.sub(r"[^A-Z0-9]", "", value.upper())
    if not key or not key[0].isalpha():
        key = f"PM{key}"
    if len(key) < 2:
        key = f"{key}PM"
    return key[:10]


def _repo_description(state: PMAgentState) -> str:
    return f"Project manager workspace for {state['project_id']}"


def provisioning_node(state: PMAgentState) -> PMAgentState:
    """Create GitHub and Jira project resources and update provisioning state."""

    repo_name = slugify_repo_name(state["project_id"])
    repo_url = create_repo(
        name=repo_name,
        description=_repo_description(state),
        private=True,
    )
    jira_project_key = create_project(
        key=slugify_jira_project_key(state["project_id"]),
        name=state["project_id"],
    )
    status_map = build_status_map(jira_project_key)

    return {
        **state,
        "github_repo_url": repo_url,
        "jira_project_key": jira_project_key,
        "status_map": status_map,
        "phase": "provisioning",
    }
