"""UI Development Server Manager for localhost pipeline."""

import logging
import os
import socket
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class UIDevServerManager:
    """Manages React development server for localhost pipeline."""

    def __init__(self, ui_source_dir: Optional[Path] = None):
        """Initialize UI dev server manager.

        Args:
            ui_source_dir: Path to UI source directory (defaults to framework UI)
        """
        self.ui_source_dir = ui_source_dir or Path(__file__).parent.parent / "ui"
        self.vite_config = self.ui_source_dir / "vite.config.ts"
        self.package_json = self.ui_source_dir / "package.json"
        self.node_modules = self.ui_source_dir / "node_modules"

        self.dev_server_process: Optional[subprocess.Popen] = None
        self.dev_server_port = (
            3080  # Less common default port, will be updated by port selection
        )
        self.agent_server_port = 8080
        self.is_running = False

    def check_prerequisites(self) -> Dict[str, Any]:
        """Check if Node.js and npm are available for dev server."""
        try:
            # Check Node.js
            node_result = subprocess.run(
                ["node", "--version"], capture_output=True, text=True, timeout=10
            )
            if node_result.returncode != 0:
                return {
                    "success": False,
                    "error": "Node.js not working properly",
                    "recommendation": "Install Node.js 18+ from https://nodejs.org/",
                }

            # Check npm
            npm_result = subprocess.run(
                ["npm", "--version"], capture_output=True, text=True, timeout=10
            )
            if npm_result.returncode != 0:
                return {
                    "success": False,
                    "error": "npm not working properly",
                    "recommendation": "Reinstall Node.js with npm included",
                }

            # Check UI source directory
            if not self.ui_source_dir.exists():
                return {
                    "success": False,
                    "error": f"UI source directory not found: {self.ui_source_dir}",
                    "recommendation": "Verify Any Agent UI installation",
                }

            # Check package.json
            if not self.package_json.exists():
                return {
                    "success": False,
                    "error": f"package.json not found: {self.package_json}",
                    "recommendation": "Verify React UI setup",
                }

            return {
                "success": True,
                "node_version": node_result.stdout.strip(),
                "npm_version": npm_result.stdout.strip(),
                "ui_source_dir": str(self.ui_source_dir),
                "message": "UI dev server prerequisites satisfied",
            }

        except FileNotFoundError:
            return {
                "success": False,
                "error": "Node.js/npm not found",
                "recommendation": "Install Node.js 18+ from https://nodejs.org/",
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Node.js/npm check timed out",
                "recommendation": "Check system performance and try again",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Prerequisite check failed: {e}",
                "recommendation": "Check system configuration",
            }

    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available for binding."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(("localhost", port))
                return True
        except (socket.error, OSError):
            return False

    def _find_available_port(
        self, start_port: int = 3080, max_attempts: int = 10
    ) -> int:
        """Find an available port starting from the given port."""
        for port in range(start_port, start_port + max_attempts):
            if self._is_port_available(port):
                return port

        # If no ports found in range, try some alternative ports (avoiding common dev server ports)
        alternative_ports = [3081, 3082, 5174, 8090, 8091]
        for port in alternative_ports:
            if self._is_port_available(port):
                return port

        raise RuntimeError(
            f"No available ports found. Tried {start_port}-{start_port + max_attempts - 1} and {alternative_ports}"
        )

    def install_dependencies(self) -> Dict[str, Any]:
        """Install npm dependencies if not present."""
        if self.node_modules.exists():
            logger.info("Dependencies already installed")
            return {"success": True, "message": "Dependencies already installed"}

        try:
            logger.info("Installing npm dependencies...")
            install_result = subprocess.run(
                ["npm", "install"],
                cwd=self.ui_source_dir,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if install_result.returncode != 0:
                return {
                    "success": False,
                    "error": f"npm install failed: {install_result.stderr}",
                    "stdout": install_result.stdout,
                    "recommendation": "Check Node.js and npm installation",
                }

            logger.info("Dependencies installed successfully")
            return {
                "success": True,
                "message": "Dependencies installed successfully",
                "stdout": install_result.stdout,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "npm install timed out (5 minutes)",
                "recommendation": "Check network connection or try again",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to install dependencies: {e}",
                "recommendation": "Check system configuration and permissions",
            }

    def generate_dev_config(self, agent_port: int) -> Dict[str, Any]:
        """Generate Vite dev config for the specific agent port.

        Args:
            agent_port: Port where agent server is running

        Returns:
            Configuration result
        """
        try:
            self.agent_server_port = agent_port

            # Create dynamic vite config content
            vite_config_content = f"""import {{ defineConfig }} from 'vite'
import react from '@vitejs/plugin-react'
import {{ resolve }} from 'path'

export default defineConfig({{
  plugins: [react()],
  resolve: {{
    alias: {{
      '@': resolve(__dirname, './src'),
    }},
  }},
  build: {{
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {{
      output: {{
        manualChunks: {{
          vendor: ['react', 'react-dom'],
          mui: ['@mui/material', '@mui/icons-material', '@emotion/react', '@emotion/styled'],
        }},
      }},
    }},
  }},
  server: {{
    port: {self.dev_server_port},
    host: true,
    proxy: {{
      '/api': {{
        target: 'http://localhost:{agent_port}',
        changeOrigin: true,
      }},
      '/chat': {{
        target: 'http://localhost:{agent_port}',
        changeOrigin: true,
      }},
      '/health': {{
        target: 'http://localhost:{agent_port}',
        changeOrigin: true,
      }},
      '/.well-known': {{
        target: 'http://localhost:{agent_port}',
        changeOrigin: true,
      }},
    }},
  }},
}})
"""

            # Write the dynamic config
            with open(self.vite_config, "w") as f:
                f.write(vite_config_content)

            logger.info(f"Generated Vite dev config with proxy to port {agent_port}")
            return {
                "success": True,
                "dev_port": self.dev_server_port,
                "agent_port": agent_port,
                "config_file": str(self.vite_config),
                "message": f"Vite config generated for agent port {agent_port}",
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate dev config: {e}",
                "recommendation": "Check file permissions and disk space",
            }

    def start_dev_server(self, agent_port: int) -> Dict[str, Any]:
        """Start the React development server.

        Args:
            agent_port: Port where agent server is running

        Returns:
            Server start result
        """
        if self.is_running:
            return {
                "success": False,
                "error": "Dev server already running",
                "dev_port": self.dev_server_port,
            }

        try:
            # Find available port for dev server
            try:
                available_port = self._find_available_port(3080)
                if available_port != self.dev_server_port:
                    logger.info(
                        f"Port 3080 unavailable, using port {available_port} instead"
                    )
                    self.dev_server_port = available_port
            except RuntimeError as e:
                return {
                    "success": False,
                    "error": f"No available ports for React dev server: {e}",
                    "recommendation": "Free up some ports (3080-3090, 5174, 8090-8091) and try again",
                }

            # Generate config for this agent port
            config_result = self.generate_dev_config(agent_port)
            if not config_result["success"]:
                return config_result

            # Install dependencies if needed
            deps_result = self.install_dependencies()
            if not deps_result["success"]:
                return deps_result

            logger.info(f"Starting React dev server on port {self.dev_server_port}...")

            # Start the dev server process
            self.dev_server_process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=self.ui_source_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=dict(os.environ, NODE_ENV="development"),
            )

            # Give it a moment to start
            time.sleep(2)

            # Check if process is still running
            if self.dev_server_process.poll() is None:
                self.is_running = True
                logger.info(
                    f"React dev server started successfully on port {self.dev_server_port}"
                )
                return {
                    "success": True,
                    "dev_port": self.dev_server_port,
                    "agent_port": agent_port,
                    "ui_url": f"http://localhost:{self.dev_server_port}",
                    "message": "React dev server running with HMR enabled",
                }
            else:
                # Process died, get error output
                stdout, stderr = self.dev_server_process.communicate()
                return {
                    "success": False,
                    "error": f"Dev server failed to start: {stderr}",
                    "stdout": stdout,
                    "recommendation": "Check port availability and dependencies",
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to start dev server: {e}",
                "recommendation": "Check system resources and permissions",
            }

    def stop_dev_server(self) -> Dict[str, Any]:
        """Stop the React development server."""
        try:
            if not self.is_running or not self.dev_server_process:
                return {
                    "success": True,
                    "message": "Dev server not running",
                }

            logger.info("Stopping React dev server...")
            self.dev_server_process.terminate()

            # Wait for graceful shutdown
            try:
                self.dev_server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Dev server didn't stop gracefully, forcing...")
                self.dev_server_process.kill()
                self.dev_server_process.wait()

            self.is_running = False
            self.dev_server_process = None

            logger.info("React dev server stopped")
            return {
                "success": True,
                "message": "React dev server stopped successfully",
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to stop dev server: {e}",
            }

    def get_status(self) -> Dict[str, Any]:
        """Get current dev server status."""
        try:
            if not self.is_running or not self.dev_server_process:
                return {
                    "running": False,
                    "message": "Dev server not running",
                }

            # Check if process is still alive
            if self.dev_server_process.poll() is not None:
                # Process died
                self.is_running = False
                self.dev_server_process = None
                return {
                    "running": False,
                    "message": "Dev server process died unexpectedly",
                }

            return {
                "running": True,
                "dev_port": self.dev_server_port,
                "agent_port": self.agent_server_port,
                "ui_url": f"http://localhost:{self.dev_server_port}",
                "pid": self.dev_server_process.pid,
                "message": "React dev server running with HMR",
            }

        except Exception as e:
            return {
                "running": False,
                "error": f"Failed to get status: {e}",
            }

    def restart_dev_server(self, agent_port: int) -> Dict[str, Any]:
        """Restart the development server.

        Args:
            agent_port: Port where agent server is running

        Returns:
            Restart result
        """
        logger.info("Restarting React dev server...")

        # Stop current server
        stop_result = self.stop_dev_server()
        if not stop_result["success"]:
            logger.warning(f"Stop failed: {stop_result.get('error')}")

        # Wait a moment
        time.sleep(1)

        # Start new server
        return self.start_dev_server(agent_port)
