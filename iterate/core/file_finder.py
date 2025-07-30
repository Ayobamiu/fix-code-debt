"""
Core file discovery functionality with error handling and progress reporting.
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from .ignore_patterns import IgnorePatterns
from .cache_manager import CacheManager
from .error_handler import ErrorHandler, ErrorSeverity
from .progress_reporter import ProgressReporter, ProgressType
from .file_types import FileTypeDetector, FileCategory, Language
from .config_manager import ConfigManager


class FileFinder:
    """Main file discovery class with comprehensive error handling and progress reporting."""
    
    def __init__(self, error_handler: Optional[ErrorHandler] = None, 
                 progress_reporter: Optional[ProgressReporter] = None,
                 cache_manager: Optional[CacheManager] = None,
                 ignore_patterns: Optional[IgnorePatterns] = None,
                 config_manager: Optional[ConfigManager] = None):
        self.error_handler = error_handler or ErrorHandler()
        self.progress_reporter = progress_reporter or ProgressReporter()
        self.cache_manager = cache_manager or CacheManager(".iterate_cache", self.error_handler)
        self.ignore_patterns = ignore_patterns or IgnorePatterns(self.error_handler)
        self.file_type_detector = FileTypeDetector(self.error_handler)
        self.config_manager = config_manager or ConfigManager(self.error_handler)
    
    def find_files_and_folders(self, directory_path: str, recursive: bool = True, 
                              max_depth: Optional[int] = None, ignore_patterns: Optional[List[str]] = None) -> Dict:
        """
        Find all files and folders in a directory with comprehensive error handling and progress reporting.
        
        Args:
            directory_path: Path to the directory to scan
            recursive: Whether to scan subdirectories
            max_depth: Maximum depth for recursive scanning
            ignore_patterns: Custom ignore patterns
            
        Returns:
            Dictionary with scan results and metadata
        """
        start_time = time.time()
        
        # Load project configuration
        project_config = self.config_manager.load_project_config(directory_path)
        scan_config = project_config.get("scan", {})
        ignore_config = project_config.get("ignore", {})
        cache_config = project_config.get("cache", {})
        progress_config = project_config.get("progress", {})
        
        # Override with function parameters if provided
        if recursive is not None:
            scan_config["recursive"] = recursive
        if max_depth is not None:
            scan_config["max_depth"] = max_depth
        
        # Validate directory
        try:
            directory_path = Path(directory_path).resolve()
            if not directory_path.exists():
                raise FileNotFoundError(f"Directory does not exist: {directory_path}")
            if not directory_path.is_dir():
                raise NotADirectoryError(f"Path is not a directory: {directory_path}")
        except Exception as e:
            self.error_handler.handle_error(
                e, 
                {"operation": "validate_directory", "path": str(directory_path)}, 
                ErrorSeverity.ERROR
            )
            return self._create_error_result(str(e))
        
        # Initialize ignore patterns with project config
        project_ignore_patterns = ignore_config.get("patterns", [])
        if ignore_patterns:
            project_ignore_patterns.extend(ignore_patterns)
        
        ignore_handler = IgnorePatterns(project_ignore_patterns, self.error_handler)
        
        # Check cache first
        if self.cache_manager and cache_config.get("enabled", True):
            cached_result = self.cache_manager.get(str(directory_path), scan_config["recursive"], 
                                                 scan_config["max_depth"], project_ignore_patterns)
            if cached_result:
                cached_result["scan_time"] = time.time() - start_time
                cached_result["errors"] = self.error_handler.get_error_summary()
                return cached_result
        
        # Start progress reporting
        self.progress_reporter.start_scan(str(directory_path))
        
        # Perform the scan
        try:
            files, folders, files_processed, directories_processed = self._perform_scan(
                directory_path, scan_config["recursive"], scan_config["max_depth"], project_ignore_patterns
            )
            
            # Get file type statistics
            file_stats = self.file_type_detector.get_file_stats(files)
            
            # Create result
            result = {
                "files": sorted(files),
                "folders": sorted(folders),
                "total_files": len(files),
                "total_folders": len(folders),
                "files_processed": files_processed,
                "directories_processed": directories_processed,
                "directory": str(directory_path),
                "file_stats": file_stats,
                "config_used": project_config
            }
            
            # Cache the result
            if self.cache_manager and cache_config.get("enabled", True):
                self.cache_manager.set(str(directory_path), scan_config["recursive"], 
                                     scan_config["max_depth"], project_ignore_patterns, result)
            
            # Add metadata
            result["scan_time"] = time.time() - start_time
            result["cached"] = False
            result["incremental"] = False
            result["errors"] = self.error_handler.get_error_summary()
            
            # Finish progress reporting
            self.progress_reporter.finish_scan(len(files), len(folders))
            
            return result
            
        except Exception as e:
            self.error_handler.handle_error(
                f"Error during scan of {directory_path}: {str(e)}",
                ErrorSeverity.ERROR
            )
            return self._create_error_result(str(e))
    
    def _perform_scan(self, directory_path: Path, recursive: bool, max_depth: int, 
                      ignore_patterns: List[str]) -> Tuple[List[str], List[str], int, int]:
        """Perform the actual file system scan."""
        files = []
        folders = []
        files_processed = 0
        directories_processed = 0
        
        try:
            if recursive:
                for root, dirs, filenames in os.walk(directory_path):
                    # Calculate current depth
                    current_depth = len(Path(root).relative_to(directory_path).parts)
                    
                    # Filter directories based on max_depth and ignore patterns
                    filtered_dirs = []
                    for dir_name in dirs:
                        dir_path = os.path.join(root, dir_name)
                        if (max_depth == -1 or current_depth < max_depth) and \
                           not self.ignore_patterns.should_ignore(dir_path, is_dir=True):
                            filtered_dirs.append(dir_name)
                            folders.append(dir_path)
                            directories_processed += 1
                        else:
                            if max_depth != -1 and current_depth >= max_depth:
                                self.error_handler.handle_error(
                                    f"Max depth {max_depth} reached at {dir_path}",
                                    ErrorSeverity.INFO
                                )
                    
                    # Update dirs list to only include non-ignored directories
                    dirs[:] = filtered_dirs
                    
                    # Process files
                    for filename in filenames:
                        file_path = os.path.join(root, filename)
                        if not self.ignore_patterns.should_ignore(file_path):
                            files.append(file_path)
                            files_processed += 1
                            
                            # Update progress
                            self.progress_reporter.update_progress(
                                current_file=filename,
                                current_directory=root,
                                files_processed=files_processed,
                                directories_processed=directories_processed,
                                total_files_found=len(files),
                                total_directories_found=len(folders)
                            )
            else:
                # Non-recursive scan
                try:
                    with os.scandir(directory_path) as entries:
                        for entry in entries:
                            if entry.is_file():
                                if not self.ignore_patterns.should_ignore(entry.path):
                                    files.append(entry.path)
                                    files_processed += 1
                            elif entry.is_dir():
                                if not self.ignore_patterns.should_ignore(entry.path, is_dir=True):
                                    folders.append(entry.path)
                                    directories_processed += 1
                                    
                            # Update progress
                            self.progress_reporter.update_progress(
                                current_file=entry.name if entry.is_file() else "",
                                current_directory=str(directory_path),
                                files_processed=files_processed,
                                directories_processed=directories_processed,
                                total_files_found=len(files),
                                total_directories_found=len(folders)
                            )
                except PermissionError as e:
                    self.error_handler.handle_error(
                        f"Permission denied accessing {directory_path}: {str(e)}",
                        ErrorSeverity.ERROR
                    )
                    raise
                    
        except Exception as e:
            self.error_handler.handle_error(
                f"Error during scan of {directory_path}: {str(e)}",
                ErrorSeverity.ERROR
            )
            raise
            
        return files, folders, files_processed, directories_processed
    
    def _create_error_result(self, error_message: str) -> Dict:
        """Create a result dictionary for error cases."""
        return {
            "files": [],
            "folders": [],
            "total_files": 0,
            "total_folders": 0,
            "error": error_message,
            "scan_time": 0.0,
            "cached": False,
            "incremental": False,
            "errors": self.error_handler.get_error_summary(),
            "directory": "N/A"
        }
    
    def get_error_summary(self) -> Dict:
        """Get a summary of all errors encountered."""
        return self.error_handler.get_error_summary()
    
    def clear_errors(self):
        """Clear all recorded errors."""
        self.error_handler.clear_errors()
    
    def get_cache_info(self) -> Dict:
        """Get information about the cache."""
        if self.cache_manager:
            return self.cache_manager.get_cache_info()
        return {"error": "Cache not enabled"}
    
    def clear_cache(self, directory: Optional[str] = None):
        """Clear cache for a specific directory or all cache."""
        if self.cache_manager:
            self.cache_manager.clear_cache(directory)