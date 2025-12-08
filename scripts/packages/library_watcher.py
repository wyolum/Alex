"""
File watcher for hot-reloading parts libraries in AlexCAD.

This module watches JSON library files for changes and triggers
automatic reloading without requiring an application restart.
"""

import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import tkinter.messagebox as messagebox


class LibraryFileHandler(FileSystemEventHandler):
    """Handler for library file change events."""
    
    def __init__(self, callback, debounce_seconds=1.0):
        """
        Initialize the handler.
        
        Args:
            callback: Function to call when a file changes
            debounce_seconds: Minimum time between reload triggers
        """
        super().__init__()
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self.last_modified = {}
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        # Only watch .json files
        if not event.src_path.endswith('.json'):
            return
        
        # Debounce - ignore rapid successive changes
        current_time = time.time()
        last_time = self.last_modified.get(event.src_path, 0)
        
        if current_time - last_time < self.debounce_seconds:
            return
        
        self.last_modified[event.src_path] = current_time
        
        # Trigger callback
        if self.callback:
            self.callback(event.src_path)


class LibraryWatcher:
    """Watches library directories for changes."""
    
    def __init__(self, watch_paths=None, callback=None):
        """
        Initialize the watcher.
        
        Args:
            watch_paths: List of paths to watch (directories or files)
            callback: Function to call when changes are detected
        """
        self.watch_paths = watch_paths or []
        self.callback = callback
        self.observer = Observer()
        self.handlers = []
        self.is_running = False
    
    def add_watch_path(self, path):
        """Add a path to watch."""
        if path not in self.watch_paths:
            self.watch_paths.append(path)
            if self.is_running:
                self._schedule_path(path)
    
    def remove_watch_path(self, path):
        """Remove a path from watching."""
        if path in self.watch_paths:
            self.watch_paths.remove(path)
    
    def _schedule_path(self, path):
        """Schedule a path for watching."""
        if os.path.isfile(path):
            # Watch the directory containing the file
            watch_dir = os.path.dirname(path)
        else:
            watch_dir = path
        
        if os.path.exists(watch_dir):
            handler = LibraryFileHandler(self.callback)
            self.handlers.append(handler)
            self.observer.schedule(handler, watch_dir, recursive=False)
    
    def start(self):
        """Start watching for changes."""
        if self.is_running:
            return
        
        for path in self.watch_paths:
            self._schedule_path(path)
        
        self.observer.start()
        self.is_running = True
    
    def stop(self):
        """Stop watching for changes."""
        if not self.is_running:
            return
        
        self.observer.stop()
        self.observer.join()
        self.is_running = False
        self.handlers.clear()
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.stop()


def create_library_watcher(library_dir, reload_callback):
    """
    Create and start a library watcher.
    
    Args:
        library_dir: Directory containing library files to watch
        reload_callback: Function to call when files change
    
    Returns:
        LibraryWatcher instance
    """
    watcher = LibraryWatcher(
        watch_paths=[library_dir],
        callback=reload_callback
    )
    watcher.start()
    return watcher


# Example usage:
if __name__ == "__main__":
    def on_change(filepath):
        print(f"File changed: {filepath}")
    
    watcher = create_library_watcher("part_libraries", on_change)
    
    try:
        print("Watching for changes... Press Ctrl+C to stop")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        watcher.stop()
        print("Stopped watching")
