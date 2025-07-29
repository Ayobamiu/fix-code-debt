"""
Ignore patterns for file filtering.
"""

import fnmatch
from pathlib import Path
from typing import List


class IgnorePatterns:
    """Handle ignore patterns for file filtering."""
    
    def __init__(self, patterns: List[str] = None):
        self.patterns = patterns or [
            # Common ignore patterns
            "node_modules",
            ".git", 
            ".gitignore",
            ".DS_Store",
            "*.log",
            "*.tmp",
            "*.swp",
            "*.swo",
            "__pycache__",
            "*.pyc",
            "*.pyo",
            "dist",
            "build",
            ".next",
            ".nuxt",
            "coverage",
            ".nyc_output",
            ".turbo",
            ".vscode",
            ".idea",
            "*.lock",
            "pnpm-lock.yaml",
            "yarn.lock",
            "package-lock.json"
        ]
    
    def should_ignore(self, path: str, is_dir: bool = False) -> bool:
        """Check if a path should be ignored."""
        path_parts = Path(path).parts
        
        for pattern in self.patterns:
            # Convert pattern to use forward slashes
            pattern = pattern.replace("\\", "/")
            path_normalized = str(path).replace("\\", "/")
            
            # Check exact match
            if fnmatch.fnmatch(path_normalized, pattern):
                return True
            
            # Check if any part of the path matches
            for part in path_parts:
                if fnmatch.fnmatch(part, pattern):
                    return True
        
        return False