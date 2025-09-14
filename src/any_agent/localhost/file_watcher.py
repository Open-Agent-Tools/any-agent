"""File watcher for localhost development with hot reload."""

import logging
import threading
import time
from pathlib import Path
from typing import Callable, Optional, Union

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None

logger = logging.getLogger(__name__)


class AgentFileWatcher:
    """Watches agent files and triggers server restart on changes."""

    def __init__(self, agent_path: Path, callback: Callable[[], None]):
        """
        Initialize the file watcher.

        Args:
            agent_path: Path to agent directory to watch
            callback: Function to call when files change
        """
        self.agent_path = agent_path
        self.callback = callback
        self.observer: Optional[Observer] = None
        self.is_watching = False

        # Files to watch (extensions and specific filenames)
        self.watch_extensions = {".py", ".env"}
        self.watch_filenames = {"requirements.txt", "pyproject.toml", "setup.py"}

        # Debounce settings to avoid multiple rapid restarts
        self.debounce_delay = 1.0  # seconds
        self._last_change_time = 0.0
        self._restart_timer: Optional[threading.Timer] = None

        if not WATCHDOG_AVAILABLE:
            logger.warning("watchdog library not available - file watching disabled")

    def start_watching(self) -> bool:
        """
        Start watching for file changes.

        Returns:
            True if watching started successfully, False otherwise
        """
        if not WATCHDOG_AVAILABLE:
            logger.error("Cannot start file watching - watchdog library not installed")
            logger.info("Install with: pip install watchdog")
            return False

        if self.is_watching:
            logger.warning("File watcher already running")
            return True

        try:
            event_handler = AgentFileEventHandler(self)
            self.observer = Observer()
            self.observer.schedule(event_handler, str(self.agent_path), recursive=True)
            self.observer.start()

            self.is_watching = True
            logger.info(f"📁 Started watching {self.agent_path} for changes...")
            logger.info(
                f"   Watching: {', '.join(self.watch_extensions)} files and {', '.join(self.watch_filenames)}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to start file watcher: {e}")
            return False

    def stop_watching(self):
        """Stop watching for file changes."""
        if not self.is_watching:
            return

        if self._restart_timer:
            self._restart_timer.cancel()
            self._restart_timer = None

        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=2.0)
            self.observer = None

        self.is_watching = False
        logger.info("📁 Stopped file watching")

    def _should_watch_file(self, file_path: Path) -> bool:
        """
        Determine if a file should trigger a restart.

        Args:
            file_path: Path to the file that changed

        Returns:
            True if file should be watched, False otherwise
        """
        # Skip hidden files and directories
        if any(part.startswith(".") for part in file_path.parts[:-1]):
            if ".any_agent" not in str(file_path):  # Allow .any_agent directory
                return False

        # Skip __pycache__ and other cache directories
        if "__pycache__" in str(file_path) or ".pyc" in str(file_path):
            return False

        # Check file extension
        if file_path.suffix.lower() in self.watch_extensions:
            return True

        # Check specific filenames
        if file_path.name in self.watch_filenames:
            return True

        return False

    def _on_file_changed(self, file_path: Path):
        """
        Handle file change event with debouncing.

        Args:
            file_path: Path to the file that changed
        """
        if not self._should_watch_file(file_path):
            return

        current_time = time.time()
        self._last_change_time = current_time

        logger.info(f"🔄 File changed: {file_path}")

        # Cancel any existing timer
        if self._restart_timer:
            self._restart_timer.cancel()

        # Start new debounced restart timer
        self._restart_timer = threading.Timer(
            self.debounce_delay, self._trigger_restart
        )
        self._restart_timer.start()

    def _trigger_restart(self):
        """Trigger server restart after debounce period."""
        try:
            logger.info("🔄 Triggering server restart due to file changes...")
            self.callback()
        except Exception as e:
            logger.error(f"Error during restart callback: {e}")
        finally:
            self._restart_timer = None


class AgentFileEventHandler(FileSystemEventHandler):
    """Event handler for file system changes."""

    def __init__(self, watcher: AgentFileWatcher):
        """Initialize event handler with watcher reference."""
        super().__init__()
        self.watcher = watcher

    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            self.watcher._on_file_changed(Path(event.src_path))

    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            self.watcher._on_file_changed(Path(event.src_path))


class FallbackFileWatcher:
    """Fallback file watcher using polling when watchdog is not available."""

    def __init__(self, agent_path: Path, callback: Callable[[], None]):
        """Initialize fallback watcher with polling."""
        self.agent_path = agent_path
        self.callback = callback
        self.is_watching = False
        self._polling_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Track file modification times
        self._file_mtimes: dict[Path, float] = {}
        self.watch_extensions = {".py", ".env"}
        self.watch_filenames = {"requirements.txt", "pyproject.toml", "setup.py"}

        logger.warning(
            "Using fallback polling file watcher (install watchdog for better performance)"
        )

    def start_watching(self) -> bool:
        """Start polling for file changes."""
        if self.is_watching:
            return True

        self._scan_files()  # Initial scan

        self.is_watching = True
        self._stop_event.clear()
        self._polling_thread = threading.Thread(target=self._polling_loop, daemon=True)
        self._polling_thread.start()

        logger.info(
            f"📁 Started polling {self.agent_path} for changes (every 2 seconds)..."
        )
        return True

    def stop_watching(self):
        """Stop polling for file changes."""
        if not self.is_watching:
            return

        self.is_watching = False
        self._stop_event.set()

        if self._polling_thread:
            self._polling_thread.join(timeout=3.0)

        logger.info("📁 Stopped file polling")

    def _scan_files(self):
        """Scan all watched files and update modification times."""
        try:
            for file_path in self.agent_path.rglob("*"):
                if file_path.is_file() and self._should_watch_file(file_path):
                    try:
                        mtime = file_path.stat().st_mtime
                        self._file_mtimes[file_path] = mtime
                    except (OSError, IOError):
                        continue
        except Exception as e:
            logger.error(f"Error scanning files: {e}")

    def _should_watch_file(self, file_path: Path) -> bool:
        """Same logic as AgentFileWatcher."""
        if any(part.startswith(".") for part in file_path.parts[:-1]):
            if ".any_agent" not in str(file_path):
                return False

        if "__pycache__" in str(file_path) or ".pyc" in str(file_path):
            return False

        if file_path.suffix.lower() in self.watch_extensions:
            return True

        if file_path.name in self.watch_filenames:
            return True

        return False

    def _polling_loop(self):
        """Main polling loop."""
        while not self._stop_event.wait(2.0):  # Poll every 2 seconds
            try:
                self._check_for_changes()
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")

    def _check_for_changes(self):
        """Check for file changes and trigger callback if found."""
        changed_files = []

        # Check existing files
        for file_path in list(self._file_mtimes.keys()):
            try:
                if file_path.exists():
                    mtime = file_path.stat().st_mtime
                    if mtime > self._file_mtimes[file_path]:
                        changed_files.append(file_path)
                        self._file_mtimes[file_path] = mtime
                else:
                    # File was deleted
                    del self._file_mtimes[file_path]
                    changed_files.append(file_path)
            except (OSError, IOError):
                continue

        # Check for new files
        for file_path in self.agent_path.rglob("*"):
            if (
                file_path.is_file()
                and self._should_watch_file(file_path)
                and file_path not in self._file_mtimes
            ):
                try:
                    mtime = file_path.stat().st_mtime
                    self._file_mtimes[file_path] = mtime
                    changed_files.append(file_path)
                except (OSError, IOError):
                    continue

        # Trigger callback if changes found
        if changed_files:
            for file_path in changed_files:
                logger.info(f"🔄 File changed: {file_path}")

            try:
                self.callback()
            except Exception as e:
                logger.error(f"Error during restart callback: {e}")


def create_file_watcher(
    agent_path: Path, callback: Callable[[], None]
) -> Union[AgentFileWatcher, "FallbackFileWatcher"]:
    """
    Create appropriate file watcher based on available libraries.

    Args:
        agent_path: Path to agent directory
        callback: Function to call on file changes

    Returns:
        File watcher instance
    """
    if WATCHDOG_AVAILABLE:
        return AgentFileWatcher(agent_path, callback)
    else:
        return FallbackFileWatcher(agent_path, callback)
