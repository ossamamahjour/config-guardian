"""File system watching for continuous validation."""

import logging
import time
from pathlib import Path
from typing import Callable

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)


class YAMLFileHandler(FileSystemEventHandler):
    """Handle YAML file change events."""
    
    def __init__(self, callback: Callable[[], None], debounce_seconds: float = 1.0):
        """
        Initialize handler.
        
        Args:
            callback: Function to call when YAML files change
            debounce_seconds: Minimum time between callback invocations
        """
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self.last_trigger = 0.0
    
    def on_any_event(self, event: FileSystemEvent) -> None:
        """Handle any file system event."""
        if event.is_directory:
            return
        
        # Only trigger on YAML files
        if not (event.src_path.endswith(".yaml") or event.src_path.endswith(".yml")):
            return
        
        # Debounce rapid successive events
        current_time = time.time()
        if current_time - self.last_trigger < self.debounce_seconds:
            return
        
        self.last_trigger = current_time
        logger.info(f"Detected change in: {event.src_path}")
        
        try:
            self.callback()
        except Exception as e:
            logger.error(f"Error in watch callback: {e}")


class FileWatcher:
    """Watch directory for YAML file changes."""
    
    def __init__(self, root_dir: str, callback: Callable[[], None]):
        """
        Initialize file watcher.
        
        Args:
            root_dir: Directory to watch
            callback: Function to call when changes detected
        """
        self.root_dir = Path(root_dir).resolve()
        self.callback = callback
        self.observer = Observer()
        self.handler = YAMLFileHandler(callback)
    
    def start(self) -> None:
        """Start watching for file changes."""
        self.observer.schedule(self.handler, str(self.root_dir), recursive=True)
        self.observer.start()
        logger.info(f"Started watching: {self.root_dir}")
        
        print(f"\n🔍 Watching {self.root_dir} for changes...")
        print("Press Ctrl+C to stop.\n")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self) -> None:
        """Stop watching for file changes."""
        self.observer.stop()
        self.observer.join()
        logger.info("Stopped file watcher")
        print("\n✓ File watcher stopped.\n")
