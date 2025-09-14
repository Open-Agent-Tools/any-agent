"""Localhost development server using uvicorn."""

import logging
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class LocalhostServer:
    """Uvicorn-based local development server with hot reload support."""

    def __init__(self):
        """Initialize the localhost server."""
        self.process: Optional[subprocess.Popen] = None
        self.app_file: Optional[Path] = None
        self.host: str = "localhost"
        self.port: int = 8080
        self.reload: bool = False

        # Restart management
        self._restart_lock = threading.RLock()
        self._restart_callback: Optional[Callable[[], None]] = None
        self._restart_count = 0

    def start_server(
        self,
        app_file: Path,
        port: int = 8080,
        host: str = "localhost",
        reload: bool = False,
        restart_callback: Optional[Callable[[], None]] = None,
    ) -> bool:
        """
        Start uvicorn server with the generated FastAPI app.

        Args:
            app_file: Path to FastAPI app file
            port: Port to run server on
            host: Host to bind to
            reload: Enable auto-reload (for future hot reload support)
            restart_callback: Callback function for regenerating app on restart

        Returns:
            True if server started successfully
        """
        with self._restart_lock:
            try:
                # Store configuration for restarts
                self.app_file = app_file
                self.host = host
                self.port = port
                self.reload = reload
                self._restart_callback = restart_callback

                return self._start_server_process()

            except Exception as e:
                logger.error(f"❌ Failed to start uvicorn server: {e}")
                return False

    def _start_server_process(self) -> bool:
        """Start the actual uvicorn server process."""
        try:
            # Construct uvicorn command
            # Use the absolute path approach with PYTHONPATH

            # Get the parent directory (agent root) and .any_agent directory
            if self.app_file is None:
                raise ValueError("App file path not set")
            agent_root = self.app_file.parent.parent
            any_agent_dir = self.app_file.parent

            # Set PYTHONPATH to include both directories
            env = dict(os.environ)
            env["PYTHONPATH"] = f"{agent_root}:{any_agent_dir}:" + env.get(
                "PYTHONPATH", ""
            )

            uvicorn_cmd = [
                sys.executable,
                "-m",
                "uvicorn",
                "localhost_app:app",
                "--host",
                self.host,
                "--port",
                str(self.port),
            ]

            if self.reload:
                uvicorn_cmd.append("--reload")

            logger.info(
                f"Starting uvicorn server with command: {' '.join(uvicorn_cmd)}"
            )
            logger.info(f"App file: {self.app_file}")
            logger.info(f"Agent root: {agent_root}")

            # Start the server process
            self.process = subprocess.Popen(
                uvicorn_cmd,
                cwd=any_agent_dir,  # Run from .any_agent directory
                env=env,  # Include PYTHONPATH environment variables
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            logger.info(f"✅ Uvicorn server started on http://{self.host}:{self.port}/")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to start uvicorn server: {e}")
            return False

    def restart_server(self) -> bool:
        """
        Gracefully restart the server with hot reload.

        Returns:
            True if restart was successful
        """
        with self._restart_lock:
            logger.info("🔄 Restarting server...")
            self._restart_count += 1

            # Stop the current server
            if not self.stop_server():
                logger.warning(
                    "Failed to stop server gracefully, continuing with restart"
                )

            # Wait a brief moment for port to be freed
            time.sleep(0.5)

            # Regenerate app if callback provided
            if self._restart_callback:
                try:
                    logger.info("🏗️  Regenerating FastAPI app...")
                    self._restart_callback()
                except Exception as e:
                    logger.error(f"❌ Failed to regenerate app: {e}")
                    return False

            # Start the new server process
            success = self._start_server_process()

            if success:
                logger.info(
                    f"✅ Server restarted successfully (restart #{self._restart_count})"
                )
            else:
                logger.error(
                    f"❌ Server restart failed (attempt #{self._restart_count})"
                )

            return success

    def is_running(self) -> bool:
        """Check if server process is still running."""
        if self.process is None:
            return False

        # Check if process is still alive
        poll = self.process.poll()
        return poll is None

    def get_server_output(self, timeout: float = 1.0) -> Optional[str]:
        """
        Get server output for logging/debugging.

        Args:
            timeout: Timeout for reading output

        Returns:
            Server output string or None
        """
        if not self.process or not self.process.stdout:
            return None

        try:
            # Use select/poll for non-blocking read with timeout
            import select

            ready, _, _ = select.select([self.process.stdout], [], [], timeout)

            if ready:
                line = self.process.stdout.readline()
                return line.strip() if line else None

        except Exception as e:
            logger.debug(f"Error reading server output: {e}")

        return None

    def stop_server(self) -> bool:
        """
        Stop the uvicorn server.

        Returns:
            True if server stopped successfully
        """
        if self.process is None:
            logger.info("No server process to stop")
            return True

        try:
            logger.info("Stopping uvicorn server...")

            # Send SIGTERM first
            self.process.terminate()

            # Wait for graceful shutdown
            try:
                self.process.wait(timeout=5)
                logger.info("✅ Server stopped gracefully")
                return True
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't stop
                logger.warning("Server didn't stop gracefully, forcing kill...")
                self.process.kill()
                self.process.wait()
                logger.info("✅ Server stopped forcefully")
                return True

        except Exception as e:
            logger.error(f"❌ Error stopping server: {e}")
            return False
        finally:
            self.process = None
            self.app_file = None
