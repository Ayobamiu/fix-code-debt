"""
GitHub MCP (Model Context Protocol) client for Iterate.
Provides direct access to GitHub's API with zero-config authentication.
"""

import os
import json
import subprocess
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GitHubRepository:
    """GitHub repository information."""
    name: str
    full_name: str
    description: Optional[str]
    language: Optional[str]
    stars: int
    forks: int
    issues: int
    pull_requests: int
    url: str


@dataclass
class GitHubIssue:
    """GitHub issue information."""
    number: int
    title: str
    body: str
    state: str
    labels: List[str]
    assignees: List[str]
    created_at: str
    url: str


class GitHubMCPClient:
    """GitHub MCP client for direct API access."""
    
    def __init__(self):
        self.authenticated = False
        self.repository = None
        self._check_authentication()
    
    def _check_authentication(self) -> bool:
        """Check if GitHub CLI is authenticated."""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and "Logged in" in result.stdout:
                self.authenticated = True
                print("✅ GitHub MCP: Using GitHub CLI authentication")
                return True
            else:
                print("⚠️  GitHub MCP: GitHub CLI not authenticated")
                return False
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ GitHub MCP: GitHub CLI not found or not working")
            return False
    
    def _run_mcp_command(self, command: str, args: List[str] = None) -> Optional[Dict[str, Any]]:
        """Run a GitHub MCP command."""
        if not self.authenticated:
            print("❌ Not authenticated with GitHub")
            return None
        
        try:
            cmd = ["gh", command] + (args or [])
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {"raw_output": result.stdout.strip()}
            else:
                print(f"❌ MCP command failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("❌ MCP command timed out")
            return None
        except Exception as e:
            print(f"❌ MCP command error: {e}")
            return None
    
    def get_current_repository(self) -> Optional[GitHubRepository]:
        """Get current repository information."""
        try:
            # Get repo info using gh repo view
            result = subprocess.run(
                ["gh", "repo", "view", "--json", "name,fullName,description,primaryLanguage,stargazerCount,forkCount,issues,openIssues,openPullRequests,url"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # Get issues count
                issues_result = subprocess.run(
                    ["gh", "issue", "list", "--json", "number"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                issues_count = 0
                if issues_result.returncode == 0:
                    issues_data = json.loads(issues_result.stdout)
                    issues_count = len(issues_data)
                
                # Get PR count
                pr_result = subprocess.run(
                    ["gh", "pr", "list", "--json", "number"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                pr_count = 0
                if pr_result.returncode == 0:
                    pr_data = json.loads(pr_result.stdout)
                    pr_count = len(pr_data)
                
                return GitHubRepository(
                    name=data.get("name", ""),
                    full_name=data.get("fullName", ""),
                    description=data.get("description"),
                    language=data.get("primaryLanguage", {}).get("name") if data.get("primaryLanguage") else None,
                    stars=data.get("stargazerCount", 0),
                    forks=data.get("forkCount", 0),
                    issues=issues_count,
                    pull_requests=pr_count,
                    url=data.get("url", "")
                )
            
            return None
            
        except Exception as e:
            print(f"❌ Failed to get repository info: {e}")
            return None
    
    def get_repository_languages(self) -> Dict[str, int]:
        """Get repository language statistics."""
        try:
            result = subprocess.run(
                ["gh", "repo", "view", "--json", "languages"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data.get("languages", {})
            
            return {}
            
        except Exception as e:
            print(f"❌ Failed to get language stats: {e}")
            return {}
    
    def get_contributors(self) -> List[Dict[str, Any]]:
        """Get repository contributors."""
        try:
            result = subprocess.run(
                ["gh", "api", "repos/:owner/:repo/contributors"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            
            return []
            
        except Exception as e:
            print(f"❌ Failed to get contributors: {e}")
            return []
    
    def get_issues(self) -> List[GitHubIssue]:
        """Get repository issues."""
        try:
            result = subprocess.run(
                ["gh", "issue", "list", "--json", "number,title,body,state,labels,assignees,createdAt,url"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return [
                    GitHubIssue(
                        number=issue["number"],
                        title=issue["title"],
                        body=issue["body"] or "",
                        state=issue["state"],
                        labels=[label["name"] for label in issue.get("labels", [])],
                        assignees=[assignee["login"] for assignee in issue.get("assignees", [])],
                        created_at=issue["createdAt"],
                        url=issue["url"]
                    )
                    for issue in data
                ]
            
            return []
            
        except Exception as e:
            print(f"❌ Failed to get issues: {e}")
            return []
    
    def create_issue(self, title: str, body: str, labels: List[str] = None) -> Optional[int]:
        """Create a new GitHub issue."""
        try:
            cmd = ["gh", "issue", "create", "--title", title, "--body", body]
            
            if labels:
                for label in labels:
                    cmd.extend(["--label", label])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Extract issue number from output
                output = result.stdout.strip()
                if "Created issue" in output:
                    # Parse issue number from output like "Created issue #123"
                    try:
                        issue_number = int(output.split("#")[-1].split()[0])
                        return issue_number
                    except (ValueError, IndexError):
                        print("⚠️  Issue created but couldn't parse issue number")
                        return None
                elif "https://github.com" in output:
                    # Parse issue number from URL like "https://github.com/owner/repo/issues/123"
                    try:
                        issue_number = int(output.split("/")[-1])
                        return issue_number
                    except (ValueError, IndexError):
                        print("⚠️  Issue created but couldn't parse issue number from URL")
                        return None
                else:
                    print(f"⚠️  Unexpected output: {output}")
                    return None
            else:
                print(f"❌ Failed to create issue: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating issue: {e}")
            return None
    
    def is_git_repository(self, directory: str = ".") -> bool:
        """Check if directory is a Git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def get_commit_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get recent commit history."""
        try:
            result = subprocess.run(
                ["gh", "api", f"repos/:owner/:repo/commits?since={days}days"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            
            return []
            
        except Exception as e:
            print(f"❌ Failed to get commit history: {e}")
            return []
    
    def get_pull_requests(self) -> List[Dict[str, Any]]:
        """Get repository pull requests."""
        try:
            result = subprocess.run(
                ["gh", "pr", "list", "--json", "number,title,body,state,labels,assignees,createdAt,url,additions,deletions"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            
            return []
            
        except Exception as e:
            print(f"❌ Failed to get pull requests: {e}")
            return []
    
    def comment_on_pr(self, pr_number: int, comment: str) -> bool:
        """Add a comment to a pull request."""
        try:
            result = subprocess.run(
                ["gh", "pr", "comment", str(pr_number), "--body", comment],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Failed to comment on PR: {e}")
            return False
    
    def get_repository_analytics(self) -> Dict[str, Any]:
        """Get comprehensive repository analytics."""
        analytics = {
            "repository": self.get_current_repository(),
            "languages": self.get_repository_languages(),
            "contributors": self.get_contributors(),
            "issues": self.get_issues(),
            "pull_requests": self.get_pull_requests(),
            "commit_history": self.get_commit_history()
        }
        
        return analytics 