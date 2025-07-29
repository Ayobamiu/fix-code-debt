"""
File system monitoring functionality.
"""

import time
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
    
    class FileChangeHandler(FileSystemEventHandler):
        """Handle file system events for real-time monitoring."""
        
        def __init__(self):
            self.changes = []
            self.start_time = time.time()
        
        def on_created(self, event):
            if not event.is_directory:
                self.changes.append(f"Created: {event.src_path}")
        
        def on_modified(self, event):
            if not event.is_directory:
                self.changes.append(f"Modified: {event.src_path}")
        
        def on_deleted(self, event):
            if not event.is_directory:
                self.changes.append(f"Deleted: {event.src_path}")
        
        def on_moved(self, event):
            if not event.is_directory:
                self.changes.append(f"Moved: {event.src_path} -> {event.dest_path}")

except ImportError:
    WATCHDOG_AVAILABLE = False
    # Create a dummy class when watchdog is not available
    class FileChangeHandler:
        def __init__(self):
            pass


def monitor_directory(directory_path: str, duration: int = 30):
    """
    Monitor a directory for file changes in real-time.
    
    Args:
        directory_path (str): Path to the directory to monitor
        duration (int): How long to monitor (seconds)
    """
    if not WATCHDOG_AVAILABLE:
        print("Error: watchdog package not available. Install with: pip install watchdog")
        return
    
    directory = Path(directory_path)
    
    if not directory.exists():
        print(f"Error: Directory does not exist: {directory_path}")
        return
    
    if not directory.is_dir():
        print(f"Error: Path is not a directory: {directory_path}")
        return
    
    print(f"🔍 Monitoring directory: {directory}")
    print(f"⏱️  Duration: {duration} seconds")
    print(f"📊 Real-time file changes will be displayed below:")
    print("=" * 60)
    
    # Set up the observer
    event_handler = FileChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, str(directory), recursive=True)
    observer.start()
    
    try:
        start_time = time.time()
        while time.time() - start_time < duration:
            time.sleep(1)
            if event_handler.changes:
                for change in event_handler.changes:
                    print(f"  🔄 {change}")
                event_handler.changes.clear()
    except KeyboardInterrupt:
        print("\n⏹️  Monitoring stopped by user.")
    finally:
        observer.stop()
        observer.join()
        print("✅ Monitoring stopped.")