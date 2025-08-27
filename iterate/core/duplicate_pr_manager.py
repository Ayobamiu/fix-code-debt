"""
Duplicate PR Manager for Iterate.
Handles grouping duplicates, user choice, and automatic PR creation.
"""

import os
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import subprocess
import tempfile

from .error_handler import ErrorHandler
from .progress_reporter import ProgressReporter


@dataclass
class DuplicateGroup:
    """A group of related duplicates for PR creation."""
    id: str
    name: str
    description: str
    duplicates: List[Dict[str, Any]]
    total_effort: str
    total_impact: str
    pattern_type: str
    files_affected: List[str]
    estimated_effort_hours: float
    severity: str
    created_at: datetime


@dataclass
class PRTemplate:
    """Template for PR creation."""
    title: str
    description: str
    branch_name: str
    labels: List[str]
    assignees: List[str]
    milestone: Optional[str] = None


class DuplicatePRManager:
    """Manages duplicate grouping and PR creation with user choice."""
    
    def __init__(self, error_handler=None):
        self.error_handler = error_handler or ErrorHandler()
        self.progress_reporter = ProgressReporter()
        self.templates_dir = ".iterate_templates"
        self.ensure_templates_dir()
    
    def ensure_templates_dir(self):
        """Ensure templates directory exists."""
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
    
    def group_duplicates(self, duplicates: List[Dict[str, Any]], max_per_group: int = 3) -> List[DuplicateGroup]:
        """Group duplicates into manageable chunks for PR creation."""
        if not duplicates:
            return []
        
        try:
            groups = []
            processed = set()
            
            # Group by pattern similarity first
            pattern_groups = self._group_by_pattern(duplicates)
            
            for pattern, pattern_dups in pattern_groups.items():
                # Split large pattern groups into smaller chunks
                chunks = self._chunk_list(pattern_dups, max_per_group)
                
                for i, chunk in enumerate(chunks):
                    if len(chunk) == 0:
                        continue
                    
                    group_id = f"group_{pattern}_{i+1}"
                    group_name = self._generate_group_name(pattern, chunk)
                    description = self._generate_group_description(chunk)
                    
                    # Calculate group metrics
                    total_effort = self._calculate_total_effort(chunk)
                    total_impact = self._assess_total_impact(chunk)
                    files_affected = self._get_files_affected(chunk)
                    estimated_hours = self._estimate_total_hours(chunk)
                    severity = self._determine_group_severity(chunk)
                    
                    group = DuplicateGroup(
                        id=group_id,
                        name=group_name,
                        description=description,
                        duplicates=chunk,
                        total_effort=total_effort,
                        total_impact=total_impact,
                        pattern_type=pattern,
                        files_affected=files_affected,
                        estimated_effort_hours=estimated_hours,
                        severity=severity,
                        created_at=datetime.now()
                    )
                    
                    groups.append(group)
            
            return groups
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "group_duplicates"})
            return []
    
    def _group_by_pattern(self, duplicates: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group duplicates by their pattern type."""
        pattern_groups = {}
        
        for duplicate in duplicates:
            pattern = duplicate.get('pattern', 'unknown')
            if pattern not in pattern_groups:
                pattern_groups[pattern] = []
            pattern_groups[pattern].append(duplicate)
        
        return pattern_groups
    
    def _chunk_list(self, items: List, chunk_size: int) -> List[List]:
        """Split a list into chunks of specified size."""
        return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
    
    def _generate_group_name(self, pattern: str, duplicates: List[Dict[str, Any]]) -> str:
        """Generate a descriptive name for a duplicate group."""
        if pattern == "input validation":
            return "Validation Logic Extraction"
        elif pattern == "error handling":
            return "Error Handling Consolidation"
        elif pattern == "file operations":
            return "File Operations Utility"
        elif pattern == "logging setup":
            return "Logging Configuration"
        elif pattern == "utility functions":
            return "Utility Function Extraction"
        elif pattern == "data processing":
            return "Data Processing Utilities"
        elif pattern == "configuration loading":
            return "Configuration Management"
        elif pattern == "API client":
            return "API Client Refactoring"
        else:
            return f"{pattern.title()} Refactoring"
    
    def _generate_group_description(self, duplicates: List[Dict[str, Any]]) -> str:
        """Generate a description for a duplicate group."""
        total_occurrences = sum(dup.get('occurrence_count', 0) for dup in duplicates)
        total_files = len(set(dup.get('target_files', [{}])[0].get('file_path', '') for dup in duplicates if dup.get('target_files')))
        
        return f"Refactor {total_occurrences} duplicate occurrences across {total_files} files"
    
    def _calculate_total_effort(self, duplicates: List[Dict[str, Any]]) -> str:
        """Calculate total effort for a group of duplicates."""
        total_hours = 0
        
        for duplicate in duplicates:
            effort = duplicate.get('estimated_effort', '1-2 hours')
            if '1-2' in effort:
                total_hours += 1.5
            elif '3-5' in effort:
                total_hours += 4
            elif '6-8' in effort:
                total_hours += 7
            elif '1-2 days' in effort:
                total_hours += 12
        
        if total_hours <= 3:
            return f"{total_hours:.1f} hours"
        elif total_hours <= 8:
            return f"{total_hours:.1f} hours"
        else:
            return f"{total_hours:.1f} hours (1+ days)"
    
    def _assess_total_impact(self, duplicates: List[Dict[str, Any]]) -> str:
        """Assess total impact for a group of duplicates."""
        high_impact_count = sum(1 for dup in duplicates if dup.get('severity') in ['critical', 'high'])
        
        if high_impact_count >= 2:
            return "High: Security, performance, or major maintenance improvements"
        elif high_impact_count >= 1:
            return "Medium: Significant maintenance reduction and consistency"
        else:
            return "Low: Code organization and minor improvements"
    
    def _get_files_affected(self, duplicates: List[Dict[str, Any]]) -> List[str]:
        """Get list of files affected by duplicates in a group."""
        files = set()
        for duplicate in duplicates:
            for target_file in duplicate.get('target_files', []):
                file_path = target_file.get('file_path', '')
                if file_path:
                    files.add(file_path)
        return list(files)
    
    def _estimate_total_hours(self, duplicates: List[Dict[str, Any]]) -> float:
        """Estimate total hours for a group of duplicates."""
        total_hours = 0
        
        for duplicate in duplicates:
            effort = duplicate.get('estimated_effort', '1-2 hours')
            if '1-2' in effort:
                total_hours += 1.5
            elif '3-5' in effort:
                total_hours += 4
            elif '6-8' in effort:
                total_hours += 7
            elif '1-2 days' in effort:
                total_hours += 12
        
        return total_hours
    
    def _determine_group_severity(self, duplicates: List[Dict[str, Any]]) -> str:
        """Determine overall severity for a group of duplicates."""
        severities = [dup.get('severity', 'low') for dup in duplicates]
        
        if 'critical' in severities:
            return 'critical'
        elif 'high' in severities:
            return 'high'
        elif 'medium' in severities:
            return 'medium'
        else:
            return 'low'
    
    def display_grouping_options(self, groups: List[DuplicateGroup]) -> None:
        """Display grouping options to the user."""
        print(f"\n🎯 Found {len(groups)} duplicate groups ready for PR creation:\n")
        
        for i, group in enumerate(groups, 1):
            severity_emoji = {
                "critical": "🔴",
                "high": "🟠", 
                "medium": "🟡",
                "low": "🟢"
            }
            
            print(f"{i}. {severity_emoji.get(group.severity, '⚪')} {group.name}")
            print(f"   📝 {group.description}")
            print(f"   ⏱️  Effort: {group.total_effort}")
            print(f"   🎯 Impact: {group.total_impact}")
            print(f"   📁 Files: {len(group.files_affected)}")
            print(f"   🔍 Pattern: {group.pattern_type}")
            print(f"   📊 Duplicates: {len(group.duplicates)}")
            print()
    
    def get_user_selection(self, groups: List[DuplicateGroup]) -> List[DuplicateGroup]:
        """Get user selection for which groups to include in PR."""
        if not groups:
            return []
        
        self.display_grouping_options(groups)
        
        while True:
            try:
                print("🎯 Select which groups to include in this PR:")
                print("   • Enter group numbers separated by commas (e.g., 1,3,5)")
                print("   • Enter 'all' for all groups")
                print("   • Enter 'q' to quit")
                print()
                
                choice = input("Your selection: ").strip().lower()
                
                if choice == 'q':
                    return []
                elif choice == 'all':
                    return groups
                else:
                    # Parse comma-separated numbers
                    selected_indices = [int(x.strip()) - 1 for x in choice.split(',')]
                    selected_groups = []
                    
                    for idx in selected_indices:
                        if 0 <= idx < len(groups):
                            selected_groups.append(groups[idx])
                        else:
                            print(f"⚠️  Invalid group number: {idx + 1}")
                    
                    if selected_groups:
                        print(f"\n✅ Selected {len(selected_groups)} groups for PR creation")
                        return selected_groups
                    else:
                        print("⚠️  No valid groups selected. Please try again.")
                        
            except ValueError:
                print("⚠️  Please enter valid numbers separated by commas")
            except KeyboardInterrupt:
                print("\n👋 Cancelled by user")
                return []
    
    def create_pr_template(self, selected_groups: List[DuplicateGroup]) -> PRTemplate:
        """Create a PR template from selected duplicate groups."""
        if not selected_groups:
            return None
        
        # Generate PR title
        total_duplicates = sum(len(group.duplicates) for group in selected_groups)
        total_effort = sum(group.estimated_effort_hours for group in selected_groups)
        
        if len(selected_groups) == 1:
            group = selected_groups[0]
            title = f"🔧 Refactor: {group.name}"
        else:
            title = f"🔧 Refactor: Eliminate {total_duplicates} duplicate code patterns"
        
        # Generate branch name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        branch_name = f"refactor/eliminate-duplicates-{timestamp}"
        
        # Generate description
        description = self._generate_pr_description(selected_groups)
        
        # Generate labels
        labels = ["refactoring", "duplicate-code", "automated"]
        
        # Add severity-based labels
        severities = [group.severity for group in selected_groups]
        if 'critical' in severities:
            labels.append("critical")
        if 'high' in severities:
            labels.append("high-priority")
        
        # Add effort-based labels
        if total_effort <= 4:
            labels.append("effort:low")
        elif total_effort <= 8:
            labels.append("effort:medium")
        else:
            labels.append("effort:high")
        
        return PRTemplate(
            title=title,
            description=description,
            branch_name=branch_name,
            labels=labels,
            assignees=[],
            milestone=None
        )
    
    def _generate_pr_description(self, selected_groups: List[DuplicateGroup]) -> str:
        """Generate detailed PR description."""
        total_duplicates = sum(len(group.duplicates) for group in selected_groups)
        total_effort = sum(group.estimated_effort_hours for group in selected_groups)
        total_files = len(set().union(*[set(group.files_affected) for group in selected_groups]))
        
        description = f"""## 📊 Summary
- **Total duplicates found:** {total_duplicates}
- **Estimated effort:** {total_effort:.1f} hours
- **Files affected:** {total_files}
- **Groups included:** {len(selected_groups)}

## 🎯 What This PR Does
This PR addresses code duplication identified by our automated analysis tool.

## 📋 Included Changes
"""
        
        for i, group in enumerate(selected_groups, 1):
            description += f"- [ ] **{group.name}** ({len(group.duplicates)} duplicates)\n"
            description += f"  - Pattern: {group.pattern_type}\n"
            description += f"  - Effort: {group.total_effort}\n"
            description += f"  - Impact: {group.total_impact}\n"
            description += f"  - Files: {', '.join(group.files_affected)}\n\n"
        
        description += """## 🔍 How to Review
1. Check each duplicate pattern is properly extracted
2. Verify new utility modules are well-tested
3. Ensure no functionality is broken
4. Validate import statements are updated

## 🧪 Testing
- [ ] All existing tests pass
- [ ] New utility functions have tests
- [ ] No regressions introduced

## 📝 Notes
- This PR was automatically generated by the Iterate tool
- Each duplicate group can be reviewed independently
- Consider merging in smaller batches if the PR becomes too large
"""
        
        return description
    
    def create_github_pr(self, pr_template: PRTemplate, selected_groups: List[DuplicateGroup]) -> bool:
        """Create a GitHub PR using the template."""
        if not pr_template or not selected_groups:
            return False
        
        try:
            print(f"🚀 Creating GitHub PR: {pr_template.title}")
            
            # Check if we're in a git repository
            if not self._is_git_repo():
                print("❌ Not in a git repository. Cannot create PR.")
                return False
            
            # Check if GitHub CLI is available
            if not self._check_gh_cli():
                print("❌ GitHub CLI not found. Please install 'gh' CLI tool.")
                return False
            
            # Create and switch to feature branch
            if not self._create_feature_branch(pr_template.branch_name):
                print("❌ Failed to create feature branch.")
                return False
            
            # Generate and apply refactoring changes
            if not self._apply_refactoring_changes(selected_groups):
                print("❌ Failed to apply refactoring changes.")
                return False
            
            # Commit changes
            if not self._commit_changes(pr_template.title):
                print("❌ Failed to commit changes.")
                return False
            
            # Push branch
            if not self._push_branch(pr_template.branch_name):
                print("❌ Failed to push branch.")
                return False
            
            # Create PR
            if not self._create_pr_with_gh(pr_template):
                print("❌ Failed to create PR with GitHub CLI.")
                return False
            
            print(f"✅ Successfully created PR: {pr_template.title}")
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "create_github_pr"})
            return False
    
    def _is_git_repo(self) -> bool:
        """Check if current directory is a git repository."""
        try:
            result = subprocess.run(['git', 'status'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _check_gh_cli(self) -> bool:
        """Check if GitHub CLI is available and authenticated."""
        try:
            result = subprocess.run(['gh', 'auth', 'status'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _create_feature_branch(self, branch_name: str) -> bool:
        """Create and switch to a feature branch."""
        try:
            # Create and switch to new branch
            result = subprocess.run(['git', 'checkout', '-b', branch_name], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def _apply_refactoring_changes(self, selected_groups: List[DuplicateGroup]) -> bool:
        """Apply refactoring changes for selected duplicate groups."""
        # This is a placeholder - in a real implementation, you would:
        # 1. Generate refactored code for each duplicate
        # 2. Apply the changes to the appropriate files
        # 3. Handle conflicts and edge cases
        
        print("📝 Applying refactoring changes...")
        print("   (This is a placeholder - actual refactoring would be implemented here)")
        
        # For now, just create a placeholder file to show the PR works
        placeholder_content = """# Refactoring Changes Applied

This file was created to demonstrate the PR creation process.
In a real implementation, this would contain the actual refactored code.

## Changes Made:
"""
        
        for group in selected_groups:
            placeholder_content += f"\n### {group.name}\n"
            placeholder_content += f"- Pattern: {group.pattern_type}\n"
            placeholder_content += f"- Duplicates: {len(group.duplicates)}\n"
            placeholder_content += f"- Files: {', '.join(group.files_affected)}\n"
        
        try:
            with open("REFACTORING_CHANGES.md", "w") as f:
                f.write(placeholder_content)
            return True
        except Exception:
            return False
    
    def _commit_changes(self, commit_message: str) -> bool:
        """Commit the refactoring changes."""
        try:
            # Add all changes
            subprocess.run(['git', 'add', '.'], capture_output=True, text=True)
            
            # Commit
            result = subprocess.run(['git', 'commit', '-m', commit_message], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def _push_branch(self, branch_name: str) -> bool:
        """Push the feature branch to remote."""
        try:
            result = subprocess.run(['git', 'push', '-u', 'origin', branch_name], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def _create_pr_with_gh(self, pr_template: PRTemplate) -> bool:
        """Create PR using GitHub CLI."""
        try:
            # Create PR with title and body
            cmd = [
                'gh', 'pr', 'create',
                '--title', pr_template.title,
                '--body', pr_template.description,
                '--head', pr_template.branch_name
            ]
            
            # Add labels if specified
            for label in pr_template.labels:
                cmd.extend(['--label', label])
            
            # Add assignees if specified
            for assignee in pr_template.assignees:
                cmd.extend(['--assignee', assignee])
            
            # Add milestone if specified
            if pr_template.milestone:
                cmd.extend(['--milestone', pr_template.milestone])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ PR created successfully!")
                print(f"   URL: {result.stdout.strip()}")
                return True
            else:
                print(f"❌ Failed to create PR: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating PR: {e}")
            return False
    
    def save_template(self, template_name: str, groups: List[DuplicateGroup]) -> bool:
        """Save a grouping template for future use."""
        try:
            template_data = {
                "name": template_name,
                "description": f"Template for {len(groups)} duplicate groups",
                "groups": [],
                "created_at": datetime.now().isoformat(),
                "criteria": "user_defined"
            }
            
            # Convert groups to dict, handling datetime serialization
            for group in groups:
                group_dict = asdict(group)
                # Convert datetime to ISO format string for JSON serialization
                if "created_at" in group_dict and isinstance(group_dict["created_at"], datetime):
                    group_dict["created_at"] = group_dict["created_at"].isoformat()
                template_data["groups"].append(group_dict)
            
            template_file = os.path.join(self.templates_dir, f"{template_name}.json")
            with open(template_file, 'w') as f:
                json.dump(template_data, f, indent=2)
            
            print(f"💾 Template '{template_name}' saved successfully")
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "save_template"})
            return False
    
    def load_template(self, template_name: str) -> List[DuplicateGroup]:
        """Load a saved grouping template."""
        try:
            template_file = os.path.join(self.templates_dir, f"{template_name}.json")
            
            if not os.path.exists(template_file):
                print(f"⚠️  Template '{template_name}' not found")
                return []
            
            with open(template_file, 'r') as f:
                template_data = json.load(f)
            
            # Convert back to DuplicateGroup objects
            groups = []
            for group_data in template_data.get("groups", []):
                # Convert datetime string back to datetime object
                if "created_at" in group_data:
                    group_data["created_at"] = datetime.fromisoformat(group_data["created_at"])
                
                group = DuplicateGroup(**group_data)
                groups.append(group)
            
            print(f"📂 Loaded template '{template_name}' with {len(groups)} groups")
            return groups
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "load_template"})
            return []
    
    def list_templates(self) -> List[str]:
        """List available grouping templates."""
        try:
            if not os.path.exists(self.templates_dir):
                return []
            
            templates = []
            for file in os.listdir(self.templates_dir):
                if file.endswith('.json'):
                    templates.append(file[:-5])  # Remove .json extension
            
            return templates
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "list_templates"})
            return []
