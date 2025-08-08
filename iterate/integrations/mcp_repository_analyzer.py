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
from ..core.advanced_metrics import AdvancedCodeAnalyzer
from ..core.code_generator import CodeGenerator


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
    refactoring_suggestions: List[Dict[str, Any]]
    quality_report: Dict[str, Any]


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
        self.advanced_analyzer = AdvancedCodeAnalyzer()
        self.code_generator = CodeGenerator()
    
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
        
        # Perform advanced quality analysis
        print("📊 Analyzing code quality metrics...")
        quality_report = self.advanced_analyzer.generate_quality_report(all_files)
        
        # Generate refactoring suggestions
        print("🤖 Generating AI-powered refactoring suggestions...")
        refactoring_suggestions = self._generate_refactoring_suggestions(all_files, quality_report)
        
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
        recommendations = self._generate_recommendations(dependencies, debt_score, quality_report)
        
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
            team_insights=team_insights,
            refactoring_suggestions=refactoring_suggestions,
            quality_report=quality_report
        )
    
    def _analyze_local_only(self, directory: str) -> MCPRepositoryAnalysis:
        """Analyze repository without GitHub integration."""
        dependencies, all_files = self.dependency_analyzer.analyze_codebase()
        file_breakdown = self._get_file_breakdown(all_files)
        debt_score = self._calculate_debt_score(dependencies, file_breakdown)
        recommendations = self._generate_recommendations(dependencies, debt_score)
        
        # Generate refactoring suggestions for local analysis
        refactoring_suggestions = self._generate_refactoring_suggestions(all_files, quality_report)
        
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
            team_insights={},
            refactoring_suggestions=refactoring_suggestions,
            quality_report=quality_report
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
    
    def _generate_recommendations(self, dependencies: Dict[str, Any], debt_score: float, quality_report: Dict[str, Any]) -> List[str]:
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
        
        # Add quality-based recommendations
        if quality_report.get('recommendations'):
            recommendations.extend(quality_report['recommendations'])
        
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
    
    def _generate_refactoring_suggestions(self, files: List[str], quality_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate AI-powered refactoring suggestions for files with high complexity."""
        suggestions = []
        
        # Get files with high complexity
        high_complexity_files = []
        for file_path, metrics in quality_report.get('complexity_metrics', {}).items():
            if hasattr(metrics, 'cyclomatic_complexity') and metrics.cyclomatic_complexity > 10:
                high_complexity_files.append(file_path)
        
        # Generate suggestions for high complexity files
        for file_path in high_complexity_files[:5]:  # Limit to top 5 files
            try:
                file_suggestions = self.code_generator.analyze_file_for_refactoring(
                    file_path, 
                    quality_report.get('complexity_metrics', {}).get(file_path, {})
                )
                
                for suggestion in file_suggestions:
                    suggestions.append({
                        'file_path': suggestion.file_path,
                        'line_number': suggestion.line_number,
                        'type': suggestion.suggestion_type,
                        'description': suggestion.description,
                        'complexity_reduction': suggestion.complexity_reduction,
                        'confidence': suggestion.confidence,
                        'original_code': suggestion.original_code[:200] + "..." if len(suggestion.original_code) > 200 else suggestion.original_code,
                        'suggested_code': suggestion.suggested_code[:200] + "..." if len(suggestion.suggested_code) > 200 else suggestion.suggested_code
                    })
                    
            except Exception as e:
                print(f"⚠️  Error generating suggestions for {file_path}: {e}")
        
        return suggestions
    
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
        
        # Add advanced quality metrics
        if hasattr(analysis, 'quality_report'):
            quality = analysis.quality_report.get('quality_scores', {})
            if hasattr(quality, 'overall_score'):
                print(f"📊 Quality Score: {quality.overall_score:.1%}")
                print(f"   Complexity: {quality.complexity_score:.1%}")
                print(f"   Duplication: {quality.duplication_score:.1%}")
                print(f"   Documentation: {quality.documentation_score:.1%}")
        
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
        
        # Show AI refactoring suggestions
        if hasattr(analysis, 'refactoring_suggestions') and analysis.refactoring_suggestions:
            print(f"\n🤖 AI Refactoring Suggestions:")
            print(f"   Found {len(analysis.refactoring_suggestions)} suggestions")
            for i, suggestion in enumerate(analysis.refactoring_suggestions[:3], 1):  # Show top 3
                print(f"   {i}. {suggestion['file_path']}: {suggestion['description']}")
                print(f"      Confidence: {suggestion['confidence']:.1%}, Complexity Reduction: {suggestion['complexity_reduction']:.1f}")
        
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