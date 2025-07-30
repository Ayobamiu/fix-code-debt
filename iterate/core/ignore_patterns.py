"""
File and directory ignore patterns for filtering during scans.
"""

import fnmatch
from pathlib import Path
from typing import List, Optional
from .error_handler import ErrorHandler, ErrorSeverity


class IgnorePatterns:
    """Handles ignore patterns for filtering files and directories."""
    
    def __init__(self, custom_patterns: Optional[List[str]] = None, error_handler: Optional[ErrorHandler] = None):
        self.error_handler = error_handler or ErrorHandler()
        
        # Default patterns for common directories/files to ignore
        self.default_patterns = [
            # Version control
            ".git",
            ".svn",
            ".hg",
            ".bzr",
            
            # Node.js
            "node_modules",
            "npm-debug.log",
            "yarn-error.log",
            "yarn.lock",
            "package-lock.json",
            
            # Python
            "__pycache__",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".Python",
            "*.so",
            ".pytest_cache",
            ".coverage",
            "htmlcov",
            ".tox",
            ".venv",
            "venv",
            "env",
            "ENV",
            
            # Build and distribution
            "build",
            "dist",
            "*.egg-info",
            "target",
            
            # IDE and editor
            ".vscode",
            ".idea",
            "*.swp",
            "*.swo",
            "*~",
            ".DS_Store",
            "Thumbs.db",
            
            # Logs and temporary files
            "*.log",
            "*.tmp",
            "*.temp",
            "logs",
            "temp",
            "tmp",
            
            # OS specific
            ".DS_Store",
            ".DS_Store?",
            "._*",
            ".Spotlight-V100",
            ".Trashes",
            "ehthumbs.db",
            "Thumbs.db",
            
            # Iterate specific
            ".iterate_cache",
            "*.cache"
        ]
        
        # Combine default and custom patterns
        self.patterns = self.default_patterns.copy()
        if custom_patterns:
            self.patterns.extend(custom_patterns)
    
    def should_ignore(self, path: str, is_dir: bool = False) -> bool:
        """
        Check if a path should be ignored based on patterns.
        
        Args:
            path: Path to check (relative or absolute)
            is_dir: Whether this is a directory
            
        Returns:
            True if path should be ignored, False otherwise
        """
        try:
            # Normalize path separators
            path_normalized = str(path).replace("\\", "/")
            path_parts = Path(path).parts
            
            for pattern in self.patterns:
                pattern = pattern.replace("\\", "/")
                
                # Check if pattern matches the full path
                if fnmatch.fnmatch(path_normalized, pattern):
                    return True
                
                # Check if pattern matches any part of the path
                for part in path_parts:
                    if fnmatch.fnmatch(part, pattern):
                        return True
                
                # Handle directory-specific patterns
                if is_dir and pattern.endswith("/"):
                    if fnmatch.fnmatch(path_normalized, pattern[:-1]):
                        return True
            
            return False
            
        except Exception as e:
            # Log error but don't fail the scan
            self.error_handler.handle_error(
                e, 
                {"path": path, "operation": "ignore_check"}, 
                ErrorSeverity.WARNING
            )
            return False
    
    def add_pattern(self, pattern: str):
        """Add a custom ignore pattern."""
        if pattern not in self.patterns:
            self.patterns.append(pattern)
    
    def remove_pattern(self, pattern: str):
        """Remove an ignore pattern."""
        if pattern in self.patterns:
            self.patterns.remove(pattern)
    
    def get_patterns(self) -> List[str]:
        """Get all current ignore patterns."""
        return self.patterns.copy()
    
    def clear_custom_patterns(self):
        """Clear all custom patterns, keeping only defaults."""
        self.patterns = self.default_patterns.copy()