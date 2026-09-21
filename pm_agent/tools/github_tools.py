"""GitHub tool functions."""

import functools
import time
from collections.abc import Callable
from typing import ParamSpec, TypeVar

from github import Github, GithubException
from requests.exceptions import RequestException

from pm_agent.config import load_settings
from pm_agent.tools.exceptions import (
    GitHubBadCredentialsError,
    GitHubRateLimitedError,
    GitHubRepoAlreadyExistsError,
    GitHubTransientNetworkError,
)


P = ParamSpec("P")
T = TypeVar("T")


def retry_transient_network_errors(
    attempts: int = 3,
    initial_delay_seconds: float = 1.0,
    backoff_factor: float = 2.0,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Retry transient network errors with exponential backoff."""

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            delay = initial_delay_seconds
            last_error: RequestException | None = None

            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except RequestException as exc:
                    last_error = exc
                    if attempt == attempts:
                        break
                    time.sleep(delay)
                    delay *= backoff_factor

            raise GitHubTransientNetworkError(
                "GitHub request failed after retrying transient network errors."
            ) from last_error

        return wrapper

    return decorator


def _raise_for_github_exception(exc: GithubException, repo_name: str) -> None:
    if exc.status == 422:
        raise GitHubRepoAlreadyExistsError(
            f"GitHub repository '{repo_name}' already exists or cannot be created."
        ) from exc
    if exc.status == 401:
        raise GitHubBadCredentialsError(
            "GitHub token is invalid, expired, or missing required permissions."
        ) from exc
    if exc.status == 403:
        raise GitHubRateLimitedError(
            "GitHub API request was rejected with 403; check rate limits and token permissions."
        ) from exc
    raise exc


@retry_transient_network_errors()
def create_repo(name: str, description: str, private: bool = True) -> str:
    """Create a GitHub repository for the authenticated user and return its URL."""

    settings = load_settings()
    github = Github(settings.github_token)

    try:
        user = github.get_user()
        repo = user.create_repo(name=name, description=description, private=private)
    except GithubException as exc:
        _raise_for_github_exception(exc, name)

    return repo.html_url

