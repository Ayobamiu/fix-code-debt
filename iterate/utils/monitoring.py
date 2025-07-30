"""
File system monitoring utilities.
"""

import time
import signal
import sys
from typing import Optional
from ..core.error_handler import ErrorHandler, ErrorSeverity


# Try to import watchdog, but provide fallback if not available
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
    
    class FileChangeHandler(FileSystemEventHandler):
        """Handle file system events with error handling."""
        
        def __init__(self, error_handler: Optional[ErrorHandler] = None):
            super().__init__()
            self.error_handler = error_handler or ErrorHandler()
            self.change_count = 0
            self.last_change_time = 0
        
        def on_created(self, event):
            """Handle file/directory creation events."""
            try:
                if not event.is_directory:
                    self.change_count += 1
                    self.last_change_time = time.time()
                    print(f"📄 Created: {event.src_path}")
            except Exception as e:
                self.error_handler.handle_error(
                    e, 
                    {"operation": "handle_created", "path": event.src_path}, 
                    ErrorSeverity.WARNING
                )
        
        def on_modified(self, event):
            """Handle file/directory modification events."""
            try:
                if not event.is_directory:
                    self.change_count += 1
                    self.last_change_time = time.time()
                    print(f"✏️  Modified: {event.src_path}")
            except Exception as e:
                self.error_handler.handle_error(
                    e, 
                    {"operation": "handle_modified", "path": event.src_path}, 
                    ErrorSeverity.WARNING
                )
        
        def on_deleted(self, event):
            """Handle file/directory deletion events."""
            try:
                if not event.is_directory:
                    self.change_count += 1
                    self.last_change_time = time.time()
                    print(f"🗑️  Deleted: {event.src_path}")
            except Exception as e:
                self.error_handler.handle_error(
                    e, 
                    {"operation": "handle_deleted", "path": event.src_path}, 
                    ErrorSeverity.WARNING
                )
        
        def on_moved(self, event):
            """Handle file/directory move events."""
            try:
                if not event.is_directory:
                    self.change_count += 1
                    self.last_change_time = time.time()
                    print(f"📦 Moved: {event.src_path} -> {event.dest_path}")
            except Exception as e:
                self.error_handler.handle_error(
                    e, 
                    {"operation": "handle_moved", "src": event.src_path, "dest": event.dest_path}, 
                    ErrorSeverity.WARNING
                )

except ImportError:
    WATCHDOG_AVAILABLE = False
    
    class FileChangeHandler:
        """Dummy file change handler when watchdog is not available."""
        
        def __init__(self, error_handler: Optional[ErrorHandler] = None):
            self.error_handler = error_handler or ErrorHandler()
            self.change_count = 0
            self.last_change_time = 0


def monitor_directory(directory_path: str, duration: Optional[int] = None, 
                    error_handler: Optional[ErrorHandler] = None):
    """
    Monitor a directory for file changes with error handling.
    
    Args:
        directory_path: Path to the directory to monitor
        duration: Duration to monitor in seconds (None for indefinite)
        error_handler: Error handler instance
    """
    if not WATCHDOG_AVAILABLE:
        print("❌ Error: watchdog library not available. Install with: pip install watchdog")
        return
    
    error_handler = error_handler or ErrorHandler()
    
    try:
        # Create event handler
        event_handler = FileChangeHandler(error_handler)
        
        # Create observer
        observer = Observer()
        observer.schedule(event_handler, directory_path, recursive=True)
        
        print(f"👀 Monitoring directory: {directory_path}")
        print("Press Ctrl+C to stop monitoring")
        print("-" * 50)
        
        # Start monitoring
        observer.start()
        
        # Set up signal handler for graceful shutdown
        def signal_handler(signum, frame):
            print("\n🛑 Stopping monitoring...")
            observer.stop()
            observer.join()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Monitor for specified duration or indefinitely
        if duration:
            print(f"⏰ Monitoring for {duration} seconds...")
            time.sleep(duration)
            observer.stop()
            observer.join()
        else:
            # Monitor indefinitely
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping monitoring...")
                observer.stop()
                observer.join()
        
        # Print summary
        print("-" * 50)
        print(f"📊 Monitoring summary:")
        print(f"   Changes detected: {event_handler.change_count}")
        if event_handler.change_count > 0:
            print(f"   Last change: {time.strftime('%H:%M:%S', time.localtime(event_handler.last_change_time))}")
        
        # Print error summary
        error_summary = error_handler.get_error_summary()
        if error_summary.get('total_errors', 0) > 0:
            print(f"   Errors: {error_summary['total_errors']}")
        
    except Exception as e:
        error_handler.handle_error(
            e, 
            {"operation": "monitor_directory", "directory": directory_path}, 
            ErrorSeverity.ERROR
        )
        print(f"❌ Error starting monitoring: {e}")