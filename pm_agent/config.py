"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


REQUIRED_ENV_VARS = (
    "DEEPSEEK_API_KEY",
    "GITHUB_TOKEN",
    "JIRA_API_TOKEN",
    "JIRA_BASE_URL",
)

DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"


@dataclass(frozen=True)
class Settings:
    """Runtime settings required by the agent and its tools."""

    deepseek_api_key: str
    deepseek_base_url: str
    github_token: str
    jira_api_token: str
    jira_base_url: str
    langchain_tracing_v2: str | None
    langchain_api_key: str | None
    langchain_project: str | None


def load_settings() -> Settings:
    """Load required settings and fail fast if any are missing."""

    load_dotenv()

    missing_vars = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing_vars:
        missing = ", ".join(missing_vars)
        raise RuntimeError(
            "Missing required environment variable(s): "
            f"{missing}. Add them to your environment or .env file before startup."
        )

    return Settings(
        deepseek_api_key=os.environ["DEEPSEEK_API_KEY"],
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL),
        github_token=os.environ["GITHUB_TOKEN"],
        jira_api_token=os.environ["JIRA_API_TOKEN"],
        jira_base_url=os.environ["JIRA_BASE_URL"],
        langchain_tracing_v2=os.getenv("LANGCHAIN_TRACING_V2"),
        langchain_api_key=os.getenv("LANGCHAIN_API_KEY"),
        langchain_project=os.getenv("LANGCHAIN_PROJECT"),
    )


def configure_langsmith_tracing() -> None:
    """Load optional LangSmith tracing env vars without requiring them."""

    load_dotenv()

    if os.getenv("LANGCHAIN_API_KEY") and not os.getenv("LANGCHAIN_TRACING_V2"):
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
