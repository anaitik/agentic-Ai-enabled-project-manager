"""Custom exceptions for external tool integrations."""


class GitHubToolError(RuntimeError):
    """Base exception for GitHub tool failures."""


class GitHubRepoAlreadyExistsError(GitHubToolError):
    """Raised when attempting to create a repository that already exists."""


class GitHubBadCredentialsError(GitHubToolError):
    """Raised when the configured GitHub token is invalid or expired."""


class GitHubRateLimitedError(GitHubToolError):
    """Raised when GitHub rejects a request because of rate limiting."""


class GitHubTransientNetworkError(GitHubToolError):
    """Raised when transient GitHub network errors persist after retries."""

