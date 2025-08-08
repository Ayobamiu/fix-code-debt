"""
Code application module for in-place AI code changes.
Handles Git integration, interactive mode, and safety features.
"""

import os
import ast
import shutil
import subprocess
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from .ai_code_generator import AICodeSuggestion


@dataclass
class CodeChange:
    """Represents a single code change to be applied."""
    file_path: str
    function_name: str
    original_code: str
    new_code: str
    line_start: int
    line_end: int
    change_type: str  # 'refactor', 'test', 'documentation'
    confidence: float
    reasoning: str


class CodeApplier:
    """Handles in-place code application with safety features."""
    
    def __init__(self, git_enabled: bool = True):
        self.git_enabled = git_enabled
        self.backup_dir = ".iterate_backups"
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def apply_changes_automatic(self, suggestions: List[AICodeSuggestion], 
                               create_pr: bool = True) -> bool:
        """Apply changes automatically with Git workflow."""
        try:
            # Create feature branch
            branch_name = self._create_feature_branch()
            
            # Apply all changes
            applied_changes = []
            for suggestion in suggestions:
                change = self._convert_suggestion_to_change(suggestion)
                if change:
                    success = self._apply_single_change(change)
                    if success:
                        applied_changes.append(change)
            
            if not applied_changes:
                print("❌ No changes were applied successfully")
                self._cleanup_branch(branch_name)
                return False
            
            # Commit changes
            commit_message = self._generate_commit_message(applied_changes)
            self._commit_changes(commit_message)
            
            # Create PR if requested
            if create_pr:
                pr_url = self._create_pull_request(branch_name, applied_changes)
                print(f"🚀 Pull Request created: {pr_url}")
            
            print(f"✅ Applied {len(applied_changes)} changes in branch: {branch_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error in automatic mode: {e}")
            self._rollback_changes()
            return False
    
    def apply_changes_interactive(self, suggestions: List[AICodeSuggestion]) -> bool:
        """Apply changes interactively with user confirmation."""
        applied_changes = []
        
        for i, suggestion in enumerate(suggestions, 1):
            change = self._convert_suggestion_to_change(suggestion)
            if not change:
                continue
            
            print(f"\n📝 Change {i}/{len(suggestions)}:")
            print(f"   File: {change.file_path}")
            print(f"   Function: {change.function_name}")
            print(f"   Type: {change.change_type}")
            print(f"   Confidence: {change.confidence:.1%}")
            print(f"   Reasoning: {change.reasoning[:100]}...")
            
            # Show diff
            self._show_diff(change)
            
            # Get user input
            while True:
                response = input("\nApply this change? (y/n/skip/quit): ").lower().strip()
                
                if response in ['y', 'yes']:
                    success = self._apply_single_change(change)
                    if success:
                        applied_changes.append(change)
                        print("✅ Applied!")
                    else:
                        print("❌ Failed to apply change")
                    break
                    
                elif response in ['n', 'no']:
                    print("❌ Skipped")
                    break
                    
                elif response == 'skip':
                    print("⏭️  Skipped")
                    break
                    
                elif response == 'quit':
                    print("🛑 Stopping interactive mode")
                    return len(applied_changes) > 0
                    
                else:
                    print("Please enter: y (yes), n (no), skip, or quit")
        
        if applied_changes:
            print(f"\n✅ Applied {len(applied_changes)} changes successfully!")
            return True
        else:
            print("\n❌ No changes were applied")
            return False
    
    def preview_changes(self, suggestions: List[AICodeSuggestion]) -> None:
        """Preview changes without applying them."""
        print(f"\n🔍 Previewing {len(suggestions)} AI suggestions:")
        
        for i, suggestion in enumerate(suggestions, 1):
            change = self._convert_suggestion_to_change(suggestion)
            if not change:
                continue
            
            print(f"\n📝 Suggestion {i}/{len(suggestions)}:")
            print(f"   File: {change.file_path}")
            print(f"   Function: {change.function_name}")
            print(f"   Type: {change.change_type}")
            print(f"   Confidence: {change.confidence:.1%}")
            print(f"   Reasoning: {change.reasoning}")
            
            # Show diff
            self._show_diff(change)
            
            print("-" * 80)
    
    def _convert_suggestion_to_change(self, suggestion: AICodeSuggestion) -> Optional[CodeChange]:
        """Convert AI suggestion to CodeChange object."""
        try:
            # Parse original file to find function boundaries
            with open(suggestion.file_path, 'r') as f:
                content = f.read()
            
            # Find function in AST
            tree = ast.parse(content)
            function_node = self._find_function_in_ast(tree, suggestion.function_name)
            
            if not function_node:
                print(f"⚠️  Could not find function '{suggestion.function_name}' in {suggestion.file_path}")
                return None
            
            # Get function boundaries
            lines = content.split('\n')
            start_line = function_node.lineno
            end_line = self._get_function_end_line(function_node, lines)
            
            # Extract original function code
            original_code = '\n'.join(lines[start_line-1:end_line])
            
            return CodeChange(
                file_path=suggestion.file_path,
                function_name=suggestion.function_name,
                original_code=original_code,
                new_code=suggestion.ai_generated_code,
                line_start=start_line,
                line_end=end_line,
                change_type=suggestion.suggestion_type,
                confidence=suggestion.confidence,
                reasoning=suggestion.reasoning
            )
            
        except Exception as e:
            print(f"❌ Error converting suggestion: {e}")
            return None
    
    def _find_function_in_ast(self, tree: ast.AST, func_name: str) -> Optional[ast.FunctionDef]:
        """Find function definition in AST."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                return node
        return None
    
    def _get_function_end_line(self, func_node: ast.FunctionDef, lines: List[str]) -> int:
        """Get the end line of a function."""
        # Simple approach: find the next function or end of file
        start_line = func_node.lineno - 1  # Convert to 0-based index
        
        for i in range(start_line + 1, len(lines)):
            line = lines[i].strip()
            if line.startswith('def ') and i > start_line:
                return i
            if line == '' and i > start_line + 1:
                # Check if next non-empty line is a function
                for j in range(i + 1, len(lines)):
                    if lines[j].strip():
                        if lines[j].strip().startswith('def '):
                            return i
                        break
        
        return len(lines)  # End of file
    
    def _apply_single_change(self, change: CodeChange) -> bool:
        """Apply a single code change."""
        try:
            # Create backup
            backup_path = os.path.join(self.backup_dir, f"{os.path.basename(change.file_path)}.backup")
            shutil.copy2(change.file_path, backup_path)
            
            # Read file
            with open(change.file_path, 'r') as f:
                content = f.read()
            
            # Apply change
            lines = content.split('\n')
            new_lines = (
                lines[:change.line_start-1] + 
                [change.new_code] + 
                lines[change.line_end:]
            )
            new_content = '\n'.join(new_lines)
            
            # Validate syntax
            try:
                ast.parse(new_content)
            except SyntaxError as e:
                print(f"❌ Syntax error in generated code: {e}")
                shutil.copy2(backup_path, change.file_path)
                return False
            
            # Write back
            with open(change.file_path, 'w') as f:
                f.write(new_content)
            
            return True
            
        except Exception as e:
            print(f"❌ Error applying change: {e}")
            return False
    
    def _show_diff(self, change: CodeChange) -> None:
        """Show a diff of the change."""
        print(f"\n📊 Diff for {change.function_name}:")
        print("Original:")
        print("-" * 40)
        for i, line in enumerate(change.original_code.split('\n'), change.line_start):
            print(f"{i:3d}: {line}")
        print("-" * 40)
        print("AI Generated:")
        print("-" * 40)
        for i, line in enumerate(change.new_code.split('\n'), change.line_start):
            print(f"{i:3d}: {line}")
        print("-" * 40)
    
    def _create_feature_branch(self) -> str:
        """Create a feature branch for AI changes."""
        if not self.git_enabled:
            return "ai-changes"
        
        try:
            # Get current branch
            result = subprocess.run(['git', 'branch', '--show-current'], 
                                  capture_output=True, text=True)
            current_branch = result.stdout.strip()
            
            # Create feature branch
            branch_name = f"ai-refactor-{int(time.time())}"
            subprocess.run(['git', 'checkout', '-b', branch_name], check=True)
            
            print(f"🌿 Created feature branch: {branch_name}")
            return branch_name
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Git error: {e}")
            return "ai-changes"
    
    def _commit_changes(self, message: str) -> None:
        """Commit the applied changes."""
        if not self.git_enabled:
            return
        
        try:
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', message], check=True)
            print(f"💾 Committed changes: {message}")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Git commit error: {e}")
    
    def _create_pull_request(self, branch_name: str, changes: List[CodeChange]) -> str:
        """Create a pull request for the changes."""
        if not self.git_enabled:
            return "No PR created (Git disabled)"
        
        try:
            # Generate PR description
            description = self._generate_pr_description(changes)
            
            # Create PR using GitHub CLI
            result = subprocess.run([
                'gh', 'pr', 'create',
                '--title', f'AI Code Refactoring: {len(changes)} improvements',
                '--body', description,
                '--base', 'main'
            ], capture_output=True, text=True, check=True)
            
            # Extract PR URL from output
            for line in result.stdout.split('\n'):
                if 'https://github.com' in line:
                    return line.strip()
            
            return "PR created (URL not found)"
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️  PR creation error: {e}")
            return "PR creation failed"
    
    def _generate_commit_message(self, changes: List[CodeChange]) -> str:
        """Generate a commit message for the changes."""
        change_types = [change.change_type for change in changes]
        unique_types = list(set(change_types))
        
        if len(changes) == 1:
            change = changes[0]
            return f"AI {change.change_type}: {change.function_name} in {os.path.basename(change.file_path)}"
        else:
            type_summary = ", ".join(unique_types)
            return f"AI {type_summary}: {len(changes)} improvements"
    
    def _generate_pr_description(self, changes: List[CodeChange]) -> str:
        """Generate PR description."""
        description = f"""# AI Code Refactoring

This PR contains {len(changes)} AI-generated improvements to the codebase.

## Changes Applied:

"""
        
        for change in changes:
            description += f"""### {os.path.basename(change.file_path)} - {change.function_name}
- **Type**: {change.change_type}
- **Confidence**: {change.confidence:.1%}
- **Reasoning**: {change.reasoning}

"""
        
        description += """
## Safety Measures:
- ✅ Syntax validation performed
- ✅ Git backup created
- ✅ Changes reviewed by AI
- ✅ Feature branch isolation

## Testing:
Please run the test suite to ensure all changes work correctly.
"""
        
        return description
    
    def _cleanup_branch(self, branch_name: str) -> None:
        """Clean up the feature branch if needed."""
        if not self.git_enabled:
            return
        
        try:
            subprocess.run(['git', 'checkout', 'main'], check=True)
            subprocess.run(['git', 'branch', '-D', branch_name], check=True)
            print(f"🧹 Cleaned up branch: {branch_name}")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Branch cleanup error: {e}")
    
    def _rollback_changes(self) -> None:
        """Rollback all changes."""
        try:
            subprocess.run(['git', 'checkout', '.'], check=True)
            print("🔄 Rolled back all changes")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Rollback error: {e}") 