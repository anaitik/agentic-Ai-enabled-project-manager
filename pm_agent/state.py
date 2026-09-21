"""Shared state schema for the project manager agent graph."""

from typing import Literal, TypedDict


class PMAgentState(TypedDict):
    """State passed between project manager graph nodes."""

    project_id: str
    user_id: str
    conversation_history: list[dict]
    proposed_features: list[dict]
    scope_approved: bool
    github_repo_url: str | None
    jira_project_key: str | None
    status_map: dict
    stories: list[dict]
    phase: Literal["scoping", "provisioning", "story_gen", "tracking"]
