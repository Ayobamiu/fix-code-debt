"""
Error handling and recovery for file discovery operations.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorHandler:
    """Handles errors during file discovery with recovery mechanisms."""
    
    def __init__(self, log_file: Optional[str] = None, verbose: bool = False):
        self.errors: List[Dict] = []
        self.recovery_attempts: Dict[str, int] = {}
        self.max_recovery_attempts = 3
        self.verbose = verbose
        
        # Setup logging
        self.logger = logging.getLogger("iterate.error_handler")
        self.logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        
        if not self.logger.handlers:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
            # File handler
            if log_file:
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
    
    def handle_error(self, error: Exception, context: Dict[str, Any], 
                    severity: ErrorSeverity = ErrorSeverity.ERROR) -> bool:
        """
        Handle an error with context and recovery logic.
        
        Returns:
            bool: True if error was handled/recovered, False if it should propagate
        """
        error_info = {
            "type": type(error).__name__,
            "message": str(error),
            "context": context,
            "severity": severity,
            "timestamp": self._get_timestamp()
        }
        
        self.errors.append(error_info)
        
        # Log the error
        log_message = f"{error_info['type']}: {error_info['message']} | Context: {context}"
        
        if severity == ErrorSeverity.INFO:
            self.logger.info(log_message)
        elif severity == ErrorSeverity.WARNING:
            self.logger.warning(log_message)
        elif severity == ErrorSeverity.ERROR:
            self.logger.error(log_message)
        elif severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        
        # Handle specific error types
        if isinstance(error, PermissionError):
            return self._handle_permission_error(error, context)
        elif isinstance(error, OSError):
            return self._handle_os_error(error, context)
        elif isinstance(error, UnicodeDecodeError):
            return self._handle_unicode_error(error, context)
        elif isinstance(error, MemoryError):
            return self._handle_memory_error(error, context)
        
        # For unknown errors, log and let them propagate
        return False
    
    def _handle_permission_error(self, error: PermissionError, context: Dict[str, Any]) -> bool:
        """Handle permission-related errors."""
        path = context.get("path", "unknown")
        operation = context.get("operation", "access")
        
        self.logger.warning(f"Permission denied: {operation} on {path}")
        
        # Skip this path and continue
        return True
    
    def _handle_os_error(self, error: OSError, context: Dict[str, Any]) -> bool:
        """Handle OS-related errors."""
        path = context.get("path", "unknown")
        operation = context.get("operation", "access")
        
        if error.errno == 2:  # No such file or directory
            self.logger.info(f"File not found: {path} (may have been deleted)")
            return True
        elif error.errno == 13:  # Permission denied
            return self._handle_permission_error(error, context)
        elif error.errno == 28:  # No space left on device
            self.logger.error(f"No space left on device while {operation} {path}")
            return False  # This is critical, let it propagate
        else:
            self.logger.warning(f"OS error {error.errno}: {operation} on {path}")
            return True
    
    def _handle_unicode_error(self, error: UnicodeDecodeError, context: Dict[str, Any]) -> bool:
        """Handle Unicode decoding errors."""
        path = context.get("path", "unknown")
        self.logger.warning(f"Unicode decode error in {path}, skipping file")
        return True
    
    def _handle_memory_error(self, error: MemoryError, context: Dict[str, Any]) -> bool:
        """Handle memory-related errors."""
        self.logger.error("Memory error occurred, attempting recovery...")
        
        # Try to free some memory
        import gc
        gc.collect()
        
        # If we have too many errors, stop processing
        if len(self.errors) > 100:
            self.logger.critical("Too many errors, stopping processing")
            return False
        
        return True
    
    def safe_operation(self, operation: Callable, context: Dict[str, Any], 
                      default_return: Any = None) -> Any:
        """
        Safely execute an operation with error handling.
        
        Args:
            operation: Function to execute
            context: Context information for error handling
            default_return: Value to return if operation fails
            
        Returns:
            Result of operation or default_return if failed
        """
        try:
            return operation()
        except Exception as e:
            handled = self.handle_error(e, context)
            if handled:
                return default_return
            else:
                raise  # Re-raise if not handled
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get a summary of all errors encountered."""
        error_counts = {}
        severity_counts = {}
        
        for error in self.errors:
            error_type = error["type"]
            severity = error["severity"].value
            
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_errors": len(self.errors),
            "error_types": error_counts,
            "severity_breakdown": severity_counts,
            "recovery_attempts": self.recovery_attempts.copy()
        }
    
    def clear_errors(self):
        """Clear all recorded errors."""
        self.errors.clear()
        self.recovery_attempts.clear()
    
    def _get_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()