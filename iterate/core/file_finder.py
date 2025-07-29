"""
Core file discovery functionality.
"""

import os
import time
from pathlib import Path
from typing import List, Dict

from .cache_manager import CacheManager
from .ignore_patterns import IgnorePatterns


class FileFinder:
    """Fast file finder using scandir for optimal performance."""
    
    def __init__(self, use_cache: bool = True):
        self.use_cache = use_cache
        self.cache_manager = CacheManager() if use_cache else None
    
    def find_files_and_folders(self, directory_path: str, recursive: bool = True, max_depth: int = None, ignore_patterns: List[str] = None) -> Dict:
        """
        Find all files and folders using scandir for optimal performance.
        
        Args:
            directory_path (str): Path to the directory
            recursive (bool): Whether to search subdirectories recursively
            max_depth (int): Maximum depth for recursive scanning (None = unlimited)
            ignore_patterns (List[str]): Custom ignore patterns
            
        Returns:
            dict: Dictionary with files and folders lists
        """
        directory = Path(directory_path)
        
        if not directory.exists():
            return {"error": f"Directory does not exist: {directory_path}"}
        
        if not directory.is_dir():
            return {"error": f"Path is not a directory: {directory_path}"}
        
        # Try to get from cache first
        if self.use_cache and self.cache_manager:
            cached_result = self.cache_manager.get(directory_path, recursive, max_depth, ignore_patterns)
            if cached_result:
                return cached_result
        
        files = []
        folders = []
        ignored_count = 0
        
        # Initialize ignore patterns
        ignore_handler = IgnorePatterns(ignore_patterns) if ignore_patterns is not None else None
        
        try:
            if recursive:
                # Use os.walk with scandir internally for better performance
                for root, dirs, filenames in os.walk(directory, followlinks=False):
                    # Calculate current depth
                    current_depth = len(Path(root).relative_to(directory).parts)
                    
                    # Skip if we've reached max depth
                    if max_depth is not None and current_depth >= max_depth:
                        continue
                    
                    # Filter directories to ignore
                    if ignore_handler:
                        dirs[:] = [d for d in dirs if not ignore_handler.should_ignore(str(Path(root) / d))]
                    
                    # Add folders
                    for dir_name in dirs:
                        dir_path = Path(root) / dir_name
                        relative_path = dir_path.relative_to(directory)
                        folders.append(str(relative_path))
                    
                    # Add files
                    for filename in filenames:
                        file_path = Path(root) / filename
                        relative_path = file_path.relative_to(directory)
                        
                        if ignore_handler and ignore_handler.should_ignore(str(relative_path)):
                            ignored_count += 1
                            continue
                        
                        files.append(str(relative_path))
            else:
                # Use scandir for top level - much faster than iterdir()
                with os.scandir(directory) as entries:
                    for entry in entries:
                        if ignore_handler and ignore_handler.should_ignore(entry.name):
                            ignored_count += 1
                            continue
                        
                        if entry.is_file():
                            files.append(entry.name)
                        elif entry.is_dir():
                            folders.append(entry.name)
            
            result = {
                "directory": str(directory),
                "files": files,
                "folders": folders,
                "total_files": len(files),
                "total_folders": len(folders),
                "ignored_count": ignored_count,
                "recursive": recursive,
                "max_depth": max_depth,
                "cached": False
            }
            
            # Cache the result
            if self.use_cache and self.cache_manager:
                self.cache_manager.set(directory_path, recursive, max_depth, ignore_patterns, result)
            
            return result
            
        except PermissionError:
            return {"error": f"Permission denied accessing: {directory_path}"}
        except Exception as e:
            return {"error": f"Error reading directory: {e}"}