"""
Cache management for file discovery results with incremental updates.
"""

import os
import time
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from .ignore_patterns import IgnorePatterns
from .error_handler import ErrorHandler, ErrorSeverity


class CacheManager:
    """Manage caching for file discovery results with incremental updates."""
    
    def __init__(self, cache_dir: str = ".iterate_cache", error_handler: Optional[ErrorHandler] = None):
        self.cache_dir = Path(cache_dir)
        self.error_handler = error_handler or ErrorHandler()
        
        # Ensure cache directory exists
        try:
            self.cache_dir.mkdir(exist_ok=True)
        except Exception as e:
            self.error_handler.handle_error(
                e, 
                {"operation": "create_cache_dir", "path": str(cache_dir)}, 
                ErrorSeverity.ERROR
            )
    
    def _get_cache_key(self, directory: str, recursive: bool, max_depth: int, ignore_patterns: List[str]) -> str:
        """Generate a unique cache key for the scan parameters."""
        try:
            key_data = {
                "directory": directory,
                "recursive": recursive,
                "max_depth": max_depth,
                "ignore_patterns": ignore_patterns or []
            }
            key_string = json.dumps(key_data, sort_keys=True)
            return hashlib.md5(key_string.encode()).hexdigest()
        except Exception as e:
            self.error_handler.handle_error(
                e, 
                {"operation": "generate_cache_key", "directory": directory}, 
                ErrorSeverity.ERROR
            )
            # Fallback to simple hash
            return hashlib.md5(directory.encode()).hexdigest()
    
    def _get_cache_file(self, cache_key: str) -> Path:
        """Get the cache file path for a given key."""
        return self.cache_dir / f"{cache_key}.json"
    
    def _get_file_timestamps(self, directory: Path, recursive: bool, max_depth: int, ignore_handler: IgnorePatterns) -> Dict[str, float]:
        """Get timestamps for all files in directory."""
        timestamps = {}
        
        def safe_stat(file_path: Path) -> Optional[float]:
            """Safely get file modification time."""
            try:
                return file_path.stat().st_mtime
            except (OSError, PermissionError) as e:
                self.error_handler.handle_error(
                    e, 
                    {"operation": "get_file_timestamp", "path": str(file_path)}, 
                    ErrorSeverity.WARNING
                )
                return None
        
        if recursive:
            try:
                for root, dirs, filenames in os.walk(directory, followlinks=False):
                    current_depth = len(Path(root).relative_to(directory).parts)
                    if max_depth is not None and current_depth >= max_depth:
                        continue
                    
                    # Filter directories
                    if ignore_handler:
                        dirs[:] = [d for d in dirs if not ignore_handler.should_ignore(str(Path(root) / d), is_dir=True)]
                    
                    for filename in filenames:
                        file_path = Path(root) / filename
                        relative_path = str(file_path.relative_to(directory))
                        
                        if ignore_handler and ignore_handler.should_ignore(relative_path):
                            continue
                        
                        mtime = safe_stat(file_path)
                        if mtime is not None:
                            timestamps[relative_path] = mtime
                            
            except Exception as e:
                self.error_handler.handle_error(
                    e, 
                    {"operation": "recursive_timestamp_scan", "directory": str(directory)}, 
                    ErrorSeverity.ERROR
                )
        else:
            try:
                with os.scandir(directory) as entries:
                    for entry in entries:
                        if ignore_handler and ignore_handler.should_ignore(entry.name):
                            continue
                        
                        mtime = safe_stat(Path(entry.path))
                        if mtime is not None:
                            timestamps[entry.name] = mtime
                            
            except Exception as e:
                self.error_handler.handle_error(
                    e, 
                    {"operation": "non_recursive_timestamp_scan", "directory": str(directory)}, 
                    ErrorSeverity.ERROR
                )
        
        return timestamps
    
    def get(self, directory: str, recursive: bool, max_depth: int, ignore_patterns: List[str]) -> Optional[Dict]:
        """Get cached result with incremental updates."""
        try:
            cache_key = self._get_cache_key(directory, recursive, max_depth, ignore_patterns)
            cache_file = self._get_cache_file(cache_key)
            
            if not cache_file.exists():
                return None
            
            # Load cached data
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                self.error_handler.handle_error(
                    e, 
                    {"operation": "load_cache", "cache_file": str(cache_file)}, 
                    ErrorSeverity.WARNING
                )
                return None
            
            directory_path = Path(directory)
            if not directory_path.exists():
                return None
            
            # Initialize ignore handler
            ignore_handler = IgnorePatterns(ignore_patterns, self.error_handler) if ignore_patterns is not None else None
            
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
                result["directory"] = directory  # Ensure directory is included
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
                "deleted_files": len(deleted_files),
                "directory": directory  # Ensure directory is included
            })
            
            # Update cache with new timestamps
            self._update_cache(directory, recursive, max_depth, ignore_patterns, result, current_timestamps)
            
            return result
            
        except Exception as e:
            self.error_handler.handle_error(
                e, 
                {"operation": "cache_get", "directory": directory}, 
                ErrorSeverity.ERROR
            )
            return None
    
    def _update_cache(self, directory: str, recursive: bool, max_depth: int, ignore_patterns: List[str], result: Dict, timestamps: Dict[str, float]):
        """Update cache without recursion."""
        try:
            cache_key = self._get_cache_key(directory, recursive, max_depth, ignore_patterns)
            cache_file = self._get_cache_file(cache_key)
            
            cache_data = {
                "cache_time": time.time(),
                "file_timestamps": timestamps,
                "result": result
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception as e:
            self.error_handler.handle_error(
                e, 
                {"operation": "update_cache", "directory": directory}, 
                ErrorSeverity.WARNING
            )
    
    def set(self, directory: str, recursive: bool, max_depth: int, ignore_patterns: List[str], result: Dict, timestamps: Optional[Dict[str, float]] = None):
        """Cache the scan result with file timestamps."""
        try:
            # Get timestamps if not provided
            if timestamps is None:
                directory_path = Path(directory)
                ignore_handler = IgnorePatterns(ignore_patterns, self.error_handler) if ignore_patterns is not None else None
                timestamps = self._get_file_timestamps(directory_path, recursive, max_depth, ignore_handler)
            
            self._update_cache(directory, recursive, max_depth, ignore_patterns, result, timestamps)
            
        except Exception as e:
            self.error_handler.handle_error(
                e, 
                {"operation": "cache_set", "directory": directory}, 
                ErrorSeverity.WARNING
            )
    
    def clear_cache(self, directory: Optional[str] = None):
        """Clear cache for a specific directory or all cache."""
        try:
            if directory:
                cache_key = self._get_cache_key(directory, True, None, [])
                cache_file = self._get_cache_file(cache_key)
                if cache_file.exists():
                    cache_file.unlink()
            else:
                # Clear all cache files
                for cache_file in self.cache_dir.glob("*.json"):
                    cache_file.unlink()
                    
        except Exception as e:
            self.error_handler.handle_error(
                e, 
                {"operation": "clear_cache", "directory": directory or "all"}, 
                ErrorSeverity.WARNING
            )
    
    def get_cache_info(self) -> Dict:
        """Get information about the cache."""
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            total_size = sum(f.stat().st_size for f in cache_files if f.exists())
            
            return {
                "cache_directory": str(self.cache_dir),
                "cache_files": len(cache_files),
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024)
            }
        except Exception as e:
            self.error_handler.handle_error(
                e, 
                {"operation": "get_cache_info"}, 
                ErrorSeverity.WARNING
            )
            return {"error": "Failed to get cache info"}