"""
Integrations package for external services like GitHub.
"""

from .github_client import GitHubClient
from .repository_analyzer import RepositoryAnalyzer
from .oauth_client import GitHubOAuthClient, OAuthConfig

__all__ = ['GitHubClient', 'RepositoryAnalyzer', 'GitHubOAuthClient', 'OAuthConfig'] 