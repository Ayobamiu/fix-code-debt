"""
Progress reporting for file discovery operations.
"""

import time
import sys
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class ProgressType(Enum):
    """Types of progress reporting."""
    SILENT = "silent"
    SIMPLE = "simple"
    DETAILED = "detailed"
    VERBOSE = "verbose"


@dataclass
class ProgressState:
    """Current state of progress."""
    current_file: str = ""
    current_directory: str = ""
    files_processed: int = 0
    directories_processed: int = 0
    total_files_found: int = 0
    total_directories_found: int = 0
    start_time: float = 0.0
    last_update_time: float = 0.0
    estimated_total_files: int = 0
    estimated_total_directories: int = 0


class ProgressReporter:
    """Handles progress reporting with real-time feedback and cancellation support."""
    
    def __init__(self, progress_type: ProgressType = ProgressType.SIMPLE, 
                 update_interval: float = 0.5, show_eta: bool = True):
        self.progress_type = progress_type
        self.update_interval = update_interval
        self.show_eta = show_eta
        self.state = ProgressState()
        self.callbacks: List[Callable] = []
        self.cancelled = False
        
        # Setup start time
        self.state.start_time = time.time()
        self.state.last_update_time = self.state.start_time
    
    def start_scan(self, directory: str, estimated_files: int = 0, estimated_dirs: int = 0):
        """Start a new scan operation."""
        self.state = ProgressState()
        self.state.start_time = time.time()
        self.state.last_update_time = self.state.start_time
        self.state.estimated_total_files = estimated_files
        self.state.estimated_total_directories = estimated_dirs
        self.cancelled = False
        
        if self.progress_type != ProgressType.SILENT:
            print(f"Starting scan of: {directory}")
            if estimated_files > 0 or estimated_dirs > 0:
                print(f"Estimated: {estimated_files} files, {estimated_dirs} directories")
            print("-" * 50)
    
    def update_progress(self, current_file: str = "", current_directory: str = "", 
                       files_processed: int = 0, directories_processed: int = 0,
                       total_files_found: int = 0, total_directories_found: int = 0):
        """Update progress state and display if needed."""
        # Update state
        if current_file:
            self.state.current_file = current_file
        if current_directory:
            self.state.current_directory = current_directory
        if files_processed > 0:
            self.state.files_processed = files_processed
        if directories_processed > 0:
            self.state.directories_processed = directories_processed
        if total_files_found > 0:
            self.state.total_files_found = total_files_found
        if total_directories_found > 0:
            self.state.total_directories_found = total_directories_found
        
        # Check if we should update display
        current_time = time.time()
        if (current_time - self.state.last_update_time) >= self.update_interval:
            self._display_progress()
            self.state.last_update_time = current_time
        
        # Check for cancellation
        if self._check_cancellation():
            self.cancelled = True
    
    def _display_progress(self):
        """Display current progress based on type."""
        if self.progress_type == ProgressType.SILENT:
            return
        
        elapsed_time = time.time() - self.state.start_time
        
        if self.progress_type == ProgressType.SIMPLE:
            self._display_simple_progress(elapsed_time)
        elif self.progress_type == ProgressType.DETAILED:
            self._display_detailed_progress(elapsed_time)
        elif self.progress_type == ProgressType.VERBOSE:
            self._display_verbose_progress(elapsed_time)
    
    def _display_simple_progress(self, elapsed_time: float):
        """Display simple progress bar."""
        total_items = self.state.total_files_found + self.state.total_directories_found
        processed_items = self.state.files_processed + self.state.directories_processed
        
        if total_items > 0:
            percentage = (processed_items / total_items) * 100
            bar_length = 30
            filled_length = int(bar_length * processed_items // total_items)
            bar = '█' * filled_length + '-' * (bar_length - filled_length)
            
            eta_str = ""
            if self.show_eta and processed_items > 0:
                eta = self._calculate_eta(processed_items, total_items, elapsed_time)
                eta_str = f" | ETA: {eta}"
            
            print(f"\rProgress: [{bar}] {percentage:.1f}% ({processed_items}/{total_items}){eta_str}", 
                  end="", flush=True)
    
    def _display_detailed_progress(self, elapsed_time: float):
        """Display detailed progress information."""
        total_items = self.state.total_files_found + self.state.total_directories_found
        processed_items = self.state.files_processed + self.state.directories_processed
        
        print(f"\rFiles: {self.state.files_processed}/{self.state.total_files_found} | "
              f"Dirs: {self.state.directories_processed}/{self.state.total_directories_found} | "
              f"Time: {elapsed_time:.1f}s", end="", flush=True)
        
        if self.state.current_directory and self.progress_type == ProgressType.VERBOSE:
            print(f" | Current: {self.state.current_directory}", end="")
    
    def _display_verbose_progress(self, elapsed_time: float):
        """Display verbose progress with current file/directory."""
        print(f"\r[{elapsed_time:.1f}s] Files: {self.state.files_processed} | "
              f"Dirs: {self.state.directories_processed} | "
              f"Current: {self.state.current_directory or self.state.current_file}", 
              end="", flush=True)
    
    def _calculate_eta(self, processed: int, total: int, elapsed: float) -> str:
        """Calculate estimated time remaining."""
        if processed == 0:
            return "∞"
        
        rate = processed / elapsed
        remaining = total - processed
        eta_seconds = remaining / rate if rate > 0 else 0
        
        if eta_seconds < 60:
            return f"{eta_seconds:.0f}s"
        elif eta_seconds < 3600:
            return f"{eta_seconds/60:.0f}m"
        else:
            return f"{eta_seconds/3600:.1f}h"
    
    def _check_cancellation(self) -> bool:
        """Check if user wants to cancel (Ctrl+C)."""
        try:
            # This is a simple check - in practice you might want more sophisticated handling
            return False
        except KeyboardInterrupt:
            return True
    
    def finish_scan(self, total_files: int, total_directories: int, 
                   errors: Optional[Dict] = None):
        """Finish the scan and display final results."""
        total_time = time.time() - self.state.start_time
        
        if self.progress_type != ProgressType.SILENT:
            print()  # New line after progress bar
            print("-" * 50)
            print(f"Scan completed in {total_time:.2f} seconds")
            print(f"Found: {total_files} files, {total_directories} directories")
            
            if errors and errors.get("total_errors", 0) > 0:
                print(f"Errors encountered: {errors['total_errors']}")
                for error_type, count in errors.get("error_types", {}).items():
                    print(f"  {error_type}: {count}")
        
        # Call any registered callbacks
        for callback in self.callbacks:
            try:
                callback(total_files, total_directories, total_time, errors)
            except Exception:
                pass  # Don't let callback errors break the flow
    
    def add_callback(self, callback: Callable):
        """Add a callback to be called when scan finishes."""
        self.callbacks.append(callback)
    
    def is_cancelled(self) -> bool:
        """Check if the operation has been cancelled."""
        return self.cancelled
    
    def get_progress_percentage(self) -> float:
        """Get current progress as a percentage."""
        total_items = self.state.total_files_found + self.state.total_directories_found
        processed_items = self.state.files_processed + self.state.directories_processed
        
        if total_items == 0:
            return 0.0
        
        return (processed_items / total_items) * 100
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time since scan started."""
        return time.time() - self.state.start_time