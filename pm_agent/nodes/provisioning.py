"""Provisioning node for creating external project resources."""

import re

from pm_agent.state import PMAgentState
from pm_agent.tools.github_tools import create_repo


def slugify_repo_name(value: str) -> str:
    """Convert project text into a GitHub-friendly repository name."""

    slug = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "pm-agent-project"


def _repo_description(state: PMAgentState) -> str:
    return f"Project manager workspace for {state['project_id']}"


def provisioning_node(state: PMAgentState) -> PMAgentState:
    """Create the project GitHub repository and update provisioning state."""

    repo_name = slugify_repo_name(state["project_id"])
    repo_url = create_repo(
        name=repo_name,
        description=_repo_description(state),
        private=True,
    )

    return {
        **state,
        "github_repo_url": repo_url,
        "phase": "provisioning",
    }

