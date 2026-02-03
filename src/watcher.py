import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.utils import setup_logging
from collections import defaultdict
from pathlib import Path

logger = setup_logging()

class AntigravityHandler(FileSystemEventHandler):
    def __init__(self, callback, config):
        self.callback = callback
        self.config = config
        self.last_events = defaultdict(float)
        self.debounce_seconds = 1.0
        self.ignore_patterns = set(config.get("ignore_patterns", []))

    def _is_ignored(self, file_path):
        # Basic implementation of ignore patterns
        # Real implementation would use fnmatch for globs
        path = Path(file_path)
        if path.name.startswith("~") or path.name.startswith("."):
            return True
        return False

    def on_created(self, event):
        if event.is_directory:
            return
        self._process_event(event)

    def on_modified(self, event):
        if event.is_directory:
            return
        self._process_event(event)

    def _process_event(self, event):
        file_path = event.src_path
        if self._is_ignored(file_path):
            return

        current_time = time.time()
        last_time = self.last_events[file_path]
        
        if current_time - last_time < self.debounce_seconds:
            return
        
        self.last_events[file_path] = current_time
        logger.info(f"File detected: {file_path}")
        self.callback(file_path)

def start_watcher(callback, config):
    paths = config.get("watch_paths", [])
    if not paths:
        logger.warning("No watch paths configured.")
        return None

    observer = Observer()
    handler = AntigravityHandler(callback, config)

    for path in paths:
        p = Path(path)
        if p.exists() and p.is_dir():
            logger.info(f"Watching: {p}")
            observer.schedule(handler, str(p), recursive=False)
        else:
            logger.warning(f"Watch path not found: {p}")

    observer.start()
    return observer
