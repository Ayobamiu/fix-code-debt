"""
Cache management for file discovery results with incremental updates.
"""

import os
import time
import json
import hashlib
from pathlib import Path
from typing import List, Dict

from .ignore_patterns import IgnorePatterns


class CacheManager:
    """Manage caching for file discovery results with incremental updates."""
    
    def __init__(self, cache_dir: str = ".iterate_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, directory: str, recursive: bool, max_depth: int, ignore_patterns: List[str]) -> str:
        """Generate a unique cache key for the scan parameters."""
        key_data = {
            "directory": directory,
            "recursive": recursive,
            "max_depth": max_depth,
            "ignore_patterns": ignore_patterns or []
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cache_file(self, cache_key: str) -> Path:
        """Get the cache file path for a given key."""
        return self.cache_dir / f"{cache_key}.json"
    
    def _get_file_timestamps(self, directory: Path, recursive: bool, max_depth: int, ignore_handler) -> Dict[str, float]:
        """Get timestamps for all files in directory."""
        timestamps = {}
        
        if recursive:
            for root, dirs, filenames in os.walk(directory, followlinks=False):
                current_depth = len(Path(root).relative_to(directory).parts)
                if max_depth is not None and current_depth >= max_depth:
                    continue
                
                # Filter directories
                if ignore_handler:
                    dirs[:] = [d for d in dirs if not ignore_handler.should_ignore(str(Path(root) / d))]
                
                for filename in filenames:
                    file_path = Path(root) / filename
                    relative_path = str(file_path.relative_to(directory))
                    
                    if ignore_handler and ignore_handler.should_ignore(relative_path):
                        continue
                    
                    try:
                        timestamps[relative_path] = file_path.stat().st_mtime
                    except (OSError, PermissionError):
                        continue
        else:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if ignore_handler and ignore_handler.should_ignore(entry.name):
                        continue
                    
                    try:
                        timestamps[entry.name] = entry.stat().st_mtime
                    except (OSError, PermissionError):
                        continue
        
        return timestamps
    
    def get(self, directory: str, recursive: bool, max_depth: int, ignore_patterns: List[str]) -> Dict:
        """Get cached result with incremental updates."""
        cache_key = self._get_cache_key(directory, recursive, max_depth, ignore_patterns)
        cache_file = self._get_cache_file(cache_key)
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            
            directory_path = Path(directory)
            if not directory_path.exists():
                return None
            
            # Initialize ignore handler
            ignore_handler = IgnorePatterns(ignore_patterns) if ignore_patterns is not None else None
            
            # Get current file timestamps
            current_timestamps = self._get_file_timestamps(directory_path, recursive, max_depth, ignore_handler)
            cached_timestamps = cached_data.get("file_timestamps", {})
            
            # Check for changes
            changed_files = []
            new_files = []
            deleted_files = []
            
            # Find changed/new files
            for file_path, current_mtime in current_timestamps.items():
                cached_mtime = cached_timestamps.get(file_path)
                if cached_mtime is None:
                    new_files.append(file_path)
                elif current_mtime > cached_mtime:
                    changed_files.append(file_path)
            
            # Find deleted files
            for file_path in cached_timestamps:
                if file_path not in current_timestamps:
                    deleted_files.append(file_path)
            
            # If no changes, return cached result
            if not changed_files and not new_files and not deleted_files:
                result = cached_data.get("result", {})
                result["cached"] = True
                result["incremental"] = False
                return result
            
            # Perform incremental update
            result = cached_data.get("result", {}).copy()
            files = set(result.get("files", []))
            folders = set(result.get("folders", []))
            
            # Remove deleted files
            for file_path in deleted_files:
                files.discard(file_path)
            
            # Add new files
            for file_path in new_files:
                files.add(file_path)
                # Add parent folders
                parent = Path(file_path).parent
                while str(parent) != ".":
                    folders.add(str(parent))
                    parent = parent.parent
            
            # Update result
            result.update({
                "files": sorted(list(files)),
                "folders": sorted(list(folders)),
                "total_files": len(files),
                "total_folders": len(folders),
                "cached": True,
                "incremental": True,
                "changed_files": len(changed_files),
                "new_files": len(new_files),
                "deleted_files": len(deleted_files)
            })
            
            # Update cache with new timestamps
            self.set(directory, recursive, max_depth, ignore_patterns, result, current_timestamps)
            
            return result
            
        except Exception:
            return None
    
    def set(self, directory: str, recursive: bool, max_depth: int, ignore_patterns: List[str], result: Dict, timestamps: Dict[str, float] = None):
        """Cache the scan result with file timestamps."""
        cache_key = self._get_cache_key(directory, recursive, max_depth, ignore_patterns)
        cache_file = self._get_cache_file(cache_key)
        
        try:
            # Get timestamps if not provided
            if timestamps is None:
                directory_path = Path(directory)
                ignore_handler = IgnorePatterns(ignore_patterns) if ignore_patterns is not None else None
                timestamps = self._get_file_timestamps(directory_path, recursive, max_depth, ignore_handler)
            
            cache_data = {
                "cache_time": time.time(),
                "file_timestamps": timestamps,
                "result": result
            }
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception:
            pass  # Silently fail if caching fails