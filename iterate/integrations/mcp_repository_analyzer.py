"""
Enhanced repository analyzer using GitHub MCP.
Provides comprehensive code debt analysis with GitHub integration.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from .mcp_client import GitHubMCPClient, GitHubRepository, GitHubIssue
from ..utils.dependency_analyzer import DependencyAnalyzer
from ..core.error_handler import ErrorHandler
from ..core.progress_reporter import ProgressReporter


@dataclass
class MCPRepositoryAnalysis:
    """Enhanced repository analysis with MCP data."""
    repository: Optional[GitHubRepository]
    dependencies: Dict[str, Any]
    file_breakdown: Dict[str, int]
    language_stats: Dict[str, int]
    contributors: List[Dict[str, Any]]
    issues: List[GitHubIssue]
    pull_requests: List[Dict[str, Any]]
    commit_history: List[Dict[str, Any]]
    debt_score: float
    recommendations: List[str]
    pr_debt_analysis: List[Dict[str, Any]]
    team_insights: Dict[str, Any]


class MCPRepositoryAnalyzer:
    """Enhanced repository analyzer using GitHub MCP."""
    
    def __init__(self, error_handler: Optional[ErrorHandler] = None):
        self.mcp_client = GitHubMCPClient()
        self.error_handler = error_handler or ErrorHandler()
        self.dependency_analyzer = DependencyAnalyzer(
            directory=".",
            error_handler=self.error_handler,
            progress_reporter=ProgressReporter()
        )
    
    def analyze_repository(self, directory: str = ".") -> MCPRepositoryAnalysis:
        """Perform comprehensive repository analysis using MCP."""
        print("🔍 Starting MCP repository analysis...")
        
        # Check if this is a Git repository
        if not self.mcp_client.is_git_repository(directory):
            print("⚠️  Not a Git repository. Running local analysis only.")
            return self._analyze_local_only(directory)
        
        # Get comprehensive GitHub data via MCP
        print("📊 Fetching GitHub repository data...")
        analytics = self.mcp_client.get_repository_analytics()
        
        repository = analytics.get("repository")
        if repository:
            print(f"📦 Repository: {repository.full_name}")
            print(f"🌍 Language: {repository.language or 'Unknown'}")
            print(f"⭐ Stars: {repository.stars}")
            print(f"🍴 Forks: {repository.forks}")
            print(f"📝 Issues: {repository.issues}")
            print(f"🔀 Pull Requests: {repository.pull_requests}")
        
        # Perform dependency analysis
        print("🔗 Analyzing code dependencies...")
        dependencies, all_files = self.dependency_analyzer.analyze_codebase()
        
        # Get file breakdown
        file_breakdown = self._get_file_breakdown(all_files)
        
        # Get language statistics
        language_stats = analytics.get("languages", {})
        
        # Get contributors
        contributors = analytics.get("contributors", [])
        
        # Get existing issues
        issues = analytics.get("issues", [])
        
        # Get pull requests
        pull_requests = analytics.get("pull_requests", [])
        
        # Get commit history
        commit_history = analytics.get("commit_history", [])
        
        # Calculate debt score
        debt_score = self._calculate_debt_score(dependencies, file_breakdown)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(dependencies, debt_score)
        
        # Analyze PR debt
        pr_debt_analysis = self._analyze_pr_debt(pull_requests, dependencies)
        
        # Generate team insights
        team_insights = self._generate_team_insights(contributors, commit_history, issues)
        
        return MCPRepositoryAnalysis(
            repository=repository,
            dependencies=dependencies,
            file_breakdown=file_breakdown,
            language_stats=language_stats,
            contributors=contributors,
            issues=issues,
            pull_requests=pull_requests,
            commit_history=commit_history,
            debt_score=debt_score,
            recommendations=recommendations,
            pr_debt_analysis=pr_debt_analysis,
            team_insights=team_insights
        )
    
    def _analyze_local_only(self, directory: str) -> MCPRepositoryAnalysis:
        """Analyze repository without GitHub integration."""
        dependencies, all_files = self.dependency_analyzer.analyze_codebase()
        file_breakdown = self._get_file_breakdown(all_files)
        debt_score = self._calculate_debt_score(dependencies, file_breakdown)
        recommendations = self._generate_recommendations(dependencies, debt_score)
        
        return MCPRepositoryAnalysis(
            repository=None,
            dependencies=dependencies,
            file_breakdown=file_breakdown,
            language_stats={},
            contributors=[],
            issues=[],
            pull_requests=[],
            commit_history=[],
            debt_score=debt_score,
            recommendations=recommendations,
            pr_debt_analysis=[],
            team_insights={}
        )
    
    def _get_file_breakdown(self, files: List[str]) -> Dict[str, int]:
        """Get breakdown of files by extension."""
        breakdown = {}
        for file_path in files:
            ext = Path(file_path).suffix.lower()
            breakdown[ext] = breakdown.get(ext, 0) + 1
        return breakdown
    
    def _calculate_debt_score(self, dependencies: Dict[str, Any], file_breakdown: Dict[str, int]) -> float:
        """Calculate code debt score based on dependencies and file structure."""
        if not dependencies:
            return 0.0
        
        total_files = len(dependencies)
        total_imports = sum(len(deps.imports) for deps in dependencies.values())
        total_exports = sum(len(deps.exports) for deps in dependencies.values())
        
        # Calculate complexity metrics
        high_complexity_files = sum(
            1 for deps in dependencies.values()
            if len(deps.imports) > 10 or len(deps.exports) > 10
        )
        
        no_dependency_files = sum(
            1 for deps in dependencies.values()
            if len(deps.imports) == 0 and len(deps.exports) == 0
        )
        
        # Debt score calculation
        complexity_score = min(high_complexity_files / max(total_files, 1), 1.0)
        dead_code_score = min(no_dependency_files / max(total_files, 1), 1.0)
        import_density = min(total_imports / max(total_files * 5, 1), 1.0)
        
        # Weighted average
        debt_score = (complexity_score * 0.4 + dead_code_score * 0.3 + import_density * 0.3)
        
        return min(debt_score, 1.0)
    
    def _generate_recommendations(self, dependencies: Dict[str, Any], debt_score: float) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        if debt_score > 0.7:
            recommendations.append("🔴 High debt detected! Consider refactoring complex dependencies.")
        elif debt_score > 0.5:
            recommendations.append("🟡 Moderate debt detected. Consider reviewing complex files.")
        else:
            recommendations.append("🟢 Low debt detected. Good code organization!")
        
        # Check for files with high dependency counts
        high_dep_files = [
            file_path for file_path, deps in dependencies.items()
            if len(deps.imports) > 10
        ]
        
        if high_dep_files:
            recommendations.append(f"📦 {len(high_dep_files)} files have high dependency counts. Consider breaking them down.")
        
        # Check for files with no dependencies (potential dead code)
        no_dep_files = [
            file_path for file_path, deps in dependencies.items()
            if len(deps.imports) == 0 and len(deps.exports) == 0
        ]
        
        if no_dep_files:
            recommendations.append(f"🧹 {len(no_dep_files)} files have no dependencies. Check for dead code.")
        
        return recommendations
    
    def _analyze_pr_debt(self, pull_requests: List[Dict[str, Any]], dependencies: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze debt in pull requests."""
        pr_analysis = []
        
        for pr in pull_requests:
            additions = pr.get("additions", 0)
            deletions = pr.get("deletions", 0)
            
            # Calculate PR debt score
            total_changes = additions + deletions
            if total_changes > 0:
                debt_ratio = additions / total_changes  # More additions = more debt
                pr_analysis.append({
                    "number": pr.get("number"),
                    "title": pr.get("title"),
                    "debt_score": debt_ratio,
                    "additions": additions,
                    "deletions": deletions,
                    "total_changes": total_changes
                })
        
        return pr_analysis
    
    def _generate_team_insights(self, contributors: List[Dict[str, Any]], commit_history: List[Dict[str, Any]], issues: List[GitHubIssue]) -> Dict[str, Any]:
        """Generate team collaboration insights."""
        insights = {
            "total_contributors": len(contributors),
            "active_contributors": len([c for c in contributors if c.get("contributions", 0) > 0]),
            "recent_commits": len(commit_history),
            "open_issues": len([i for i in issues if i.state == "open"]),
            "closed_issues": len([i for i in issues if i.state == "closed"])
        }
        
        return insights
    
    def print_analysis_summary(self, analysis: MCPRepositoryAnalysis):
        """Print comprehensive analysis summary."""
        print("\n" + "="*60)
        print("📊 MCP REPOSITORY ANALYSIS SUMMARY")
        print("="*60)
        
        if analysis.repository:
            print(f"📦 Repository: {analysis.repository.full_name}")
            print(f"🌍 Primary Language: {analysis.repository.language or 'Unknown'}")
            print(f"⭐ Stars: {analysis.repository.stars}")
            print(f"🍴 Forks: {analysis.repository.forks}")
            print(f"📝 Issues: {analysis.repository.issues}")
            print(f"🔀 Pull Requests: {analysis.repository.pull_requests}")
        
        print(f"\n📁 File Breakdown:")
        for ext, count in sorted(analysis.file_breakdown.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {ext}: {count} files")
        
        if analysis.language_stats and isinstance(analysis.language_stats, dict):
            print(f"\n🌍 Language Statistics:")
            for lang, bytes_count in sorted(analysis.language_stats.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"   {lang}: {bytes_count:,} bytes")
        
        print(f"\n🔗 Dependency Analysis:")
        total_files = len(analysis.dependencies)
        total_imports = sum(len(deps.imports) for deps in analysis.dependencies.values())
        total_exports = sum(len(deps.exports) for deps in analysis.dependencies.values())
        
        print(f"   Files analyzed: {total_files}")
        print(f"   Total imports: {total_imports}")
        print(f"   Total exports: {total_exports}")
        
        print(f"\n💰 Debt Score: {analysis.debt_score:.1%}")
        
        print(f"\n💡 Recommendations:")
        for rec in analysis.recommendations:
            print(f"   {rec}")
        
        if analysis.contributors:
            print(f"\n👥 Team Insights:")
            print(f"   Total contributors: {analysis.team_insights.get('total_contributors', 0)}")
            print(f"   Active contributors: {analysis.team_insights.get('active_contributors', 0)}")
            print(f"   Recent commits: {analysis.team_insights.get('recent_commits', 0)}")
            print(f"   Open issues: {analysis.team_insights.get('open_issues', 0)}")
            print(f"   Closed issues: {analysis.team_insights.get('closed_issues', 0)}")
        
        if analysis.pr_debt_analysis:
            print(f"\n🔀 Pull Request Debt Analysis:")
            high_debt_prs = [pr for pr in analysis.pr_debt_analysis if pr["debt_score"] > 0.7]
            if high_debt_prs:
                print(f"   High debt PRs: {len(high_debt_prs)}")
                for pr in high_debt_prs[:3]:  # Show top 3
                    print(f"     PR #{pr['number']}: {pr['title']} (Debt: {pr['debt_score']:.1%})")
        
        print("="*60)
    
    def create_debt_issues(self, analysis: MCPRepositoryAnalysis, auto_create: bool = False) -> List[int]:
        """Create GitHub issues for debt findings using MCP."""
        if not self.mcp_client.authenticated:
            print("❌ Not authenticated with GitHub. Cannot create issues.")
            return []
        
        issues_created = []
        
        # Create issue for high debt score
        if analysis.debt_score > 0.5:  # Lower threshold for testing
            title = f"High Code Debt Detected ({analysis.debt_score:.1%})"
            body = f"""
## Code Debt Analysis

**Debt Score:** {analysis.debt_score:.1%}

### Findings:
- {len(analysis.dependencies)} files analyzed
- {sum(len(deps.imports) for deps in analysis.dependencies.values())} total imports
- {sum(len(deps.exports) for deps in analysis.dependencies.values())} total exports

### Recommendations:
{chr(10).join(f"- {rec}" for rec in analysis.recommendations)}

### Team Insights:
- Contributors: {analysis.team_insights.get('total_contributors', 0)}
- Recent commits: {analysis.team_insights.get('recent_commits', 0)}
- Open issues: {analysis.team_insights.get('open_issues', 0)}

---
*Generated by Iterate Code Debt Tool with GitHub MCP*
            """.strip()
            
            issue_number = self.mcp_client.create_issue(title=title, body=body)
            
            if issue_number:
                issues_created.append(issue_number)
                print(f"✅ Created issue #{issue_number} for high debt score")
        
        # Create issues for high debt PRs
        high_debt_prs = [pr for pr in analysis.pr_debt_analysis if pr["debt_score"] > 0.8]
        for pr in high_debt_prs[:2]:  # Limit to 2 issues
            title = f"High Debt in PR #{pr['number']} ({pr['debt_score']:.1%})"
            body = f"""
## Pull Request Debt Analysis

**PR:** #{pr['number']} - {pr['title']}
**Debt Score:** {pr['debt_score']:.1%}

### Changes:
- Additions: {pr['additions']}
- Deletions: {pr['deletions']}
- Total changes: {pr['total_changes']}

### Recommendation:
This PR introduces significant new code. Consider:
- Breaking down large changes into smaller PRs
- Adding more tests for new functionality
- Reviewing for potential code duplication

---
*Generated by Iterate Code Debt Tool with GitHub MCP*
            """.strip()
            
            issue_number = self.mcp_client.create_issue(title=title, body=body)
            
            if issue_number:
                issues_created.append(issue_number)
                print(f"✅ Created issue #{issue_number} for high debt PR #{pr['number']}")
        
        return issues_created
    
    def comment_on_high_debt_prs(self, analysis: MCPRepositoryAnalysis) -> int:
        """Comment on pull requests with high debt."""
        if not self.mcp_client.authenticated:
            print("❌ Not authenticated with GitHub. Cannot comment on PRs.")
            return 0
        
        commented_count = 0
        high_debt_prs = [pr for pr in analysis.pr_debt_analysis if pr["debt_score"] > 0.7]
        
        for pr in high_debt_prs:
            comment = f"""
## Code Debt Analysis

This PR has a debt score of **{pr['debt_score']:.1%}**.

### Analysis:
- Additions: {pr['additions']} lines
- Deletions: {pr['deletions']} lines
- Total changes: {pr['total_changes']} lines

### Recommendations:
- Consider breaking down large changes
- Add comprehensive tests
- Review for code duplication
- Consider pair programming for complex changes

---
*Generated by Iterate Code Debt Tool*
            """.strip()
            
            if self.mcp_client.comment_on_pr(pr["number"], comment):
                commented_count += 1
                print(f"✅ Commented on PR #{pr['number']}")
        
        return commented_count 