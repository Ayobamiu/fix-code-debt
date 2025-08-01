"""
Repository analyzer that combines GitHub data with dependency analysis.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from .github_client import GitHubClient, GitHubRepository
from ..utils.dependency_analyzer import DependencyAnalyzer
from ..core.error_handler import ErrorHandler
from ..core.progress_reporter import ProgressReporter


@dataclass
class RepositoryAnalysis:
    """Complete repository analysis with GitHub and dependency data."""
    repository: Optional[GitHubRepository]
    dependencies: Dict[str, Any]
    file_breakdown: Dict[str, int]
    language_stats: Dict[str, int]
    contributors: List[Dict[str, Any]]
    issues: List[Dict[str, Any]]
    debt_score: float
    recommendations: List[str]


class RepositoryAnalyzer:
    """Analyzes repositories with GitHub integration."""
    
    def __init__(self, error_handler: Optional[ErrorHandler] = None):
        self.github_client = GitHubClient()
        self.error_handler = error_handler or ErrorHandler()
        self.dependency_analyzer = DependencyAnalyzer(
            directory=".",
            error_handler=self.error_handler,
            progress_reporter=ProgressReporter()
        )
    
    def analyze_repository(self, directory: str = ".") -> RepositoryAnalysis:
        """Perform complete repository analysis."""
        print("🔍 Starting repository analysis...")
        
        # Check if this is a Git repository
        if not self.github_client.is_git_repository(directory):
            print("⚠️  Not a Git repository. Running local analysis only.")
            return self._analyze_local_only(directory)
        
        # Get GitHub repository info
        repository = self.github_client.get_current_repository()
        if repository:
            print(f"📦 Repository: {repository.full_name}")
            print(f"🌍 Language: {repository.language or 'Unknown'}")
            print(f"⭐ Stars: {repository.stars}")
            print(f"🍴 Forks: {repository.forks}")
        
        # Perform dependency analysis
        print("🔗 Analyzing dependencies...")
        dependencies, all_files = self.dependency_analyzer.analyze_codebase()
        
        # Get file breakdown
        file_breakdown = self._get_file_breakdown(all_files)
        
        # Get language statistics
        language_stats = self.github_client.get_repository_languages()
        
        # Get contributors
        contributors = self.github_client.get_contributors()
        
        # Get existing issues
        issues = self.github_client.get_issues()
        
        # Calculate debt score
        debt_score = self._calculate_debt_score(dependencies, file_breakdown)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(dependencies, debt_score)
        
        return RepositoryAnalysis(
            repository=repository,
            dependencies=dependencies,
            file_breakdown=file_breakdown,
            language_stats=language_stats,
            contributors=contributors,
            issues=issues,
            debt_score=debt_score,
            recommendations=recommendations
        )
    
    def _analyze_local_only(self, directory: str) -> RepositoryAnalysis:
        """Analyze repository without GitHub integration."""
        dependencies, all_files = self.dependency_analyzer.analyze_codebase()
        file_breakdown = self._get_file_breakdown(all_files)
        debt_score = self._calculate_debt_score(dependencies, file_breakdown)
        recommendations = self._generate_recommendations(dependencies, debt_score)
        
        return RepositoryAnalysis(
            repository=None,
            dependencies=dependencies,
            file_breakdown=file_breakdown,
            language_stats={},
            contributors=[],
            issues=[],
            debt_score=debt_score,
            recommendations=recommendations
        )
    
    def _get_file_breakdown(self, files: List[str]) -> Dict[str, int]:
        """Get breakdown of file types."""
        breakdown = {}
        for file_path in files:
            ext = Path(file_path).suffix.lower()
            breakdown[ext] = breakdown.get(ext, 0) + 1
        return breakdown
    
    def _calculate_debt_score(self, dependencies: Dict[str, Any], file_breakdown: Dict[str, int]) -> float:
        """Calculate a debt score based on dependencies and file structure."""
        score = 0.0
        
        # Factor 1: Number of dependencies (more = higher debt potential)
        total_deps = sum(len(deps.imports) for deps in dependencies.values())
        score += min(total_deps / 100.0, 0.3)  # Cap at 30%
        
        # Factor 2: File complexity (many small files vs few large files)
        total_files = sum(file_breakdown.values())
        if total_files > 0:
            avg_deps_per_file = total_deps / total_files
            score += min(avg_deps_per_file / 10.0, 0.3)  # Cap at 30%
        
        # Factor 3: Language diversity (more languages = higher complexity)
        language_count = len(file_breakdown)
        score += min(language_count / 10.0, 0.2)  # Cap at 20%
        
        # Factor 4: Circular dependencies (if we detect them)
        # TODO: Implement circular dependency detection
        score += 0.0
        
        return min(score, 1.0)  # Cap at 100%
    
    def _generate_recommendations(self, dependencies: Dict[str, Any], debt_score: float) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        if debt_score > 0.7:
            recommendations.append("🔴 High debt detected! Consider refactoring complex dependencies.")
        elif debt_score > 0.4:
            recommendations.append("🟡 Moderate debt detected. Review dependency structure.")
        else:
            recommendations.append("🟢 Low debt detected. Good job!")
        
        # Check for files with many dependencies
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
    
    def print_analysis_summary(self, analysis: RepositoryAnalysis):
        """Print a comprehensive analysis summary."""
        print("\n" + "="*60)
        print("📊 REPOSITORY ANALYSIS SUMMARY")
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
            print(f"\n👥 Contributors: {len(analysis.contributors)}")
        
        print("="*60)
    
    def create_debt_issues(self, analysis: RepositoryAnalysis, auto_create: bool = False) -> List[int]:
        """Create GitHub issues for debt findings."""
        if not self.github_client.authenticated:
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

---
*Generated by Iterate Code Debt Tool*
            """.strip()
            
            issue_number = self.github_client.create_issue(
                title=title,
                body=body
                # No labels for now to avoid label issues
            )
            
            if issue_number:
                issues_created.append(issue_number)
                print(f"✅ Created issue #{issue_number} for high debt score")
        
        return issues_created 