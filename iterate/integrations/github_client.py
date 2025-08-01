"""
GitHub API client for repository analysis and integration.
"""

import subprocess
import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
from .oauth_client import GitHubOAuthClient


@dataclass
class GitHubRepository:
    """Repository information from GitHub."""
    name: str
    full_name: str
    description: Optional[str]
    language: Optional[str]
    languages: Dict[str, int]
    stars: int
    forks: int
    issues: int
    pull_requests: int
    last_commit: str
    size: int
    topics: List[str]


class GitHubClient:
    """GitHub API client using OAuth authentication."""
    
    def __init__(self):
        self.oauth_client = GitHubOAuthClient()
        self.authenticated = False
        self._check_authentication()
    
    def _check_authentication(self) -> bool:
        """Check if user is authenticated with OAuth."""
        # Try to load existing token first
        if self.oauth_client.load_token():
            self.authenticated = True
            return True
        
        # Fallback to GitHub CLI for backward compatibility
        try:
            result = subprocess.run(
                ['gh', 'auth', 'status'],
                capture_output=True,
                text=True,
                timeout=10
            )
            self.authenticated = result.returncode == 0
            return self.authenticated
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.authenticated = False
            return False
    
    def authenticate(self) -> bool:
        """Authenticate with GitHub using OAuth."""
        try:
            print("🔐 Starting GitHub OAuth authentication...")
            
            # Try OAuth authentication first
            if self.oauth_client.authenticate():
                self.authenticated = True
                return True
            
            # Fallback to GitHub CLI for backward compatibility
            print("🔄 Falling back to GitHub CLI authentication...")
            result = subprocess.run(
                ['gh', 'auth', 'login'],
                input='\n'.join(['GitHub.com', 'HTTPS', 'Y', 'web']),
                text=True,
                capture_output=True,
                timeout=60
            )
            if result.returncode == 0:
                self.authenticated = True
                print("✅ Successfully authenticated with GitHub CLI!")
                return True
            else:
                print(f"❌ Authentication failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print("❌ Authentication timed out")
            return False
        except FileNotFoundError:
            print("❌ GitHub CLI not found. Please install it first:")
            print("   https://cli.github.com/")
            return False
    
    def get_current_repository(self) -> Optional[GitHubRepository]:
        """Get information about the current repository."""
        if not self.authenticated:
            return None
        
        try:
            # Get repository info
            result = subprocess.run(
                ['gh', 'repo', 'view', '--json', 'name,fullName,description,primaryLanguage,languages,stargazerCount,forkCount,issues,pullRequests,defaultBranchRef,diskUsage,repositoryTopics'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return None
            
            data = json.loads(result.stdout)
            
            return GitHubRepository(
                name=data.get('name', ''),
                full_name=data.get('fullName', ''),
                description=data.get('description'),
                language=data.get('primaryLanguage', {}).get('name') if data.get('primaryLanguage') else None,
                languages=data.get('languages', {}),
                stars=data.get('stargazerCount', 0),
                forks=data.get('forkCount', 0),
                issues=data.get('issues', {}).get('totalCount', 0),
                pull_requests=data.get('pullRequests', {}).get('totalCount', 0),
                last_commit=data.get('defaultBranchRef', {}).get('target', {}).get('committedDate', ''),
                size=data.get('diskUsage', 0),
                topics=[topic.get('name', '') for topic in data.get('repositoryTopics', {}).get('nodes', [])]
            )
            
        except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError):
            return None
    
    def get_repository_languages(self) -> Dict[str, int]:
        """Get language statistics for the current repository."""
        if not self.authenticated:
            return {}
        
        try:
            result = subprocess.run(
                ['gh', 'repo', 'view', '--json', 'languages'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {}
            
            data = json.loads(result.stdout)
            return data.get('languages', {})
            
        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            return {}
    
    def get_issues(self, labels: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get issues from the current repository."""
        if not self.authenticated:
            return []
        
        try:
            cmd = ['gh', 'issue', 'list', '--json', 'number,title,state,labels,createdAt,updatedAt,author']
            if labels:
                for label in labels:
                    cmd.extend(['--label', label])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return []
            
            return json.loads(result.stdout)
            
        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            return []
    
    def create_issue(self, title: str, body: str, labels: Optional[List[str]] = None) -> Optional[int]:
        """Create a new issue in the current repository."""
        if not self.authenticated:
            return None
        
        try:
            cmd = ['gh', 'issue', 'create', '--title', title, '--body', body]
            if labels:
                for label in labels:
                    cmd.extend(['--label', label])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            

            
            if result.returncode != 0:
                print(f"❌ Failed to create issue: {result.stderr}")
                return None
            
            # Extract issue number from output
            output = result.stdout.strip()
            if 'Created issue #' in output:
                issue_number = output.split('#')[1].split()[0]
                return int(issue_number)
            elif 'https://github.com/' in output and '/issues/' in output:
                # Extract issue number from URL
                issue_number = output.split('/issues/')[1]
                return int(issue_number)
            
            return None
            
        except (subprocess.TimeoutExpired, ValueError):
            return None
    
    def get_contributors(self) -> List[Dict[str, Any]]:
        """Get contributors to the current repository."""
        if not self.authenticated:
            return []
        
        try:
            result = subprocess.run(
                ['gh', 'repo', 'view', '--json', 'collaborators'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return []
            
            data = json.loads(result.stdout)
            return data.get('collaborators', {}).get('nodes', [])
            
        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            return []
    
    def is_git_repository(self, path: str) -> bool:
        """Check if the given path is a Git repository."""
        git_dir = Path(path) / '.git'
        return git_dir.exists() and git_dir.is_dir()
    
    def get_remote_url(self, path: str) -> Optional[str]:
        """Get the remote URL for a Git repository."""
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            return None
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return None 