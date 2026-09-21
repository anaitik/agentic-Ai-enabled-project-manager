from dataclasses import dataclass

import pytest
from github import GithubException

import pm_agent.tools.github_tools as github_tools
from pm_agent.nodes.provisioning import slugify_repo_name
from pm_agent.tools.exceptions import (
    GitHubBadCredentialsError,
    GitHubRepoAlreadyExistsError,
)


@dataclass
class FakeSettings:
    github_token: str = "token"


@dataclass
class FakeRepo:
    html_url: str


class FakeUser:
    def __init__(self, repo=None, error=None):
        self.repo = repo
        self.error = error

    def create_repo(self, name, description, private):
        if self.error:
            raise self.error
        return self.repo


class FakeGithub:
    user = FakeUser(FakeRepo("https://github.com/test-owner/test-repo"))

    def __init__(self, token):
        self.token = token

    def get_user(self):
        return self.user


def _github_exception(status):
    return GithubException(status=status, data={}, headers={})


def test_create_repo_success(monkeypatch):
    FakeGithub.user = FakeUser(FakeRepo("https://github.com/test-owner/test-repo"))
    monkeypatch.setattr(github_tools, "Github", FakeGithub)
    monkeypatch.setattr(github_tools, "load_settings", lambda: FakeSettings())

    result = github_tools.create_repo(
        name="test-repo",
        description="A test repo",
        private=True,
    )

    assert result == "https://github.com/test-owner/test-repo"


def test_create_repo_already_exists(monkeypatch):
    FakeGithub.user = FakeUser(error=_github_exception(422))
    monkeypatch.setattr(github_tools, "Github", FakeGithub)
    monkeypatch.setattr(github_tools, "load_settings", lambda: FakeSettings())

    with pytest.raises(GitHubRepoAlreadyExistsError):
        github_tools.create_repo(
            name="existing-repo",
            description="A duplicate repo",
            private=True,
        )


def test_create_repo_bad_token(monkeypatch):
    FakeGithub.user = FakeUser(error=_github_exception(401))
    monkeypatch.setattr(github_tools, "Github", FakeGithub)
    monkeypatch.setattr(github_tools, "load_settings", lambda: FakeSettings())

    with pytest.raises(GitHubBadCredentialsError):
        github_tools.create_repo(
            name="test-repo",
            description="A test repo",
            private=True,
        )


def test_slugify_repo_name():
    assert slugify_repo_name("My Cool Project!") == "my-cool-project"
    assert slugify_repo_name("  Agentic   PM___System  ") == "agentic-pm-system"
    assert slugify_repo_name("!!!") == "pm-agent-project"
