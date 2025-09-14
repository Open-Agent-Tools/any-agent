"""UI Build Manager for Any Agent framework."""

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class UIBuildManager:
    """Manages the React SPA build process for Any Agent UI."""

    def __init__(self):
        self.ui_source_dir = Path(__file__).parent
        self.dist_dir = self.ui_source_dir / "dist"
        self.package_json = self.ui_source_dir / "package.json"

    def is_ui_built(self) -> bool:
        """Check if UI is already built."""
        if not self.dist_dir.exists():
            return False

        # Check for essential build files
        essential_files = ["index.html", "assets"]
        for file_name in essential_files:
            if not (self.dist_dir / file_name).exists():
                return False

        return True

    def is_pypi_installation(self) -> bool:
        """Check if this is a PyPI installation (no source files)."""
        return not self.package_json.exists()

    def should_rebuild_ui(self, force_rebuild: bool = False) -> bool:
        """Determine if UI should be rebuilt."""
        # Check if this is a PyPI installation
        if self.is_pypi_installation():
            if self.is_ui_built():
                logger.info("PyPI installation detected - using pre-built UI assets")
                return False
            else:
                logger.warning(
                    "PyPI installation detected but no pre-built UI assets found"
                )
                return False

        if force_rebuild:
            logger.info("Force rebuild requested via --rebuild-ui flag")
            return True

        if not self.is_ui_built():
            logger.info("UI not built yet - rebuild needed")
            return True

        logger.info("UI already built - skipping rebuild")
        return False

    def build_ui(self) -> Dict[str, Any]:
        """Build the React SPA UI."""
        # Check if this is a PyPI installation
        if self.is_pypi_installation():
            if self.is_ui_built():
                logger.info(
                    "PyPI installation detected - using existing pre-built UI assets"
                )
                return {
                    "success": True,
                    "message": "Using pre-built UI assets from PyPI package",
                    "dist_dir": str(self.dist_dir),
                }
            else:
                logger.error(
                    "PyPI installation detected but no pre-built UI assets found"
                )
                return {
                    "success": False,
                    "error": "No pre-built UI assets available in PyPI installation",
                    "recommendation": "Reinstall package or contact support",
                }

        logger.info(f"Building UI from {self.ui_source_dir}")

        # Check if package.json exists (for development installs)
        if not self.package_json.exists():
            return {
                "success": False,
                "error": f"package.json not found at {self.package_json}",
                "recommendation": "Run from Any Agent root directory",
            }

        try:
            # Install dependencies if node_modules doesn't exist
            node_modules = self.ui_source_dir / "node_modules"
            if not node_modules.exists():
                logger.info("Installing npm dependencies...")
                install_result = subprocess.run(
                    ["npm", "install"],
                    cwd=self.ui_source_dir,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout for npm install
                )

                if install_result.returncode != 0:
                    return {
                        "success": False,
                        "error": f"npm install failed: {install_result.stderr}",
                        "stdout": install_result.stdout,
                        "recommendation": "Check Node.js and npm installation",
                    }

                logger.info("Dependencies installed successfully")

            # Run the build
            logger.info("Building React application...")
            build_result = subprocess.run(
                ["npm", "run", "build"],
                cwd=self.ui_source_dir,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout for build
            )

            if build_result.returncode != 0:
                return {
                    "success": False,
                    "error": f"npm run build failed: {build_result.stderr}",
                    "stdout": build_result.stdout,
                    "recommendation": "Check build errors and fix TypeScript/React issues",
                }

            # Verify build output
            if not self.is_ui_built():
                return {
                    "success": False,
                    "error": "Build completed but output files not found",
                    "recommendation": "Check Vite configuration and output directory",
                }

            # Get build stats
            dist_size = self._get_directory_size(self.dist_dir)

            return {
                "success": True,
                "dist_dir": str(self.dist_dir),
                "build_size_mb": round(dist_size / 1024 / 1024, 2),
                "stdout": build_result.stdout,
                "message": "React SPA built successfully",
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Build process timed out (5 minutes)",
                "recommendation": "Check for hanging processes or network issues",
            }
        except FileNotFoundError as e:
            if "npm" in str(e):
                return {
                    "success": False,
                    "error": "npm not found - Node.js not installed",
                    "recommendation": "Install Node.js 18+ and npm",
                }
            else:
                return {
                    "success": False,
                    "error": f"File not found: {e}",
                    "recommendation": "Check file paths and permissions",
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected build error: {e}",
                "recommendation": "Check logs and system configuration",
            }

    def clean_build(self) -> Dict[str, Any]:
        """Clean existing build artifacts."""
        try:
            if self.dist_dir.exists():
                shutil.rmtree(self.dist_dir)
                logger.info(f"Cleaned build directory: {self.dist_dir}")

            node_modules = self.ui_source_dir / "node_modules"
            if node_modules.exists():
                shutil.rmtree(node_modules)
                logger.info(f"Cleaned node_modules: {node_modules}")

            return {"success": True, "message": "Build artifacts cleaned successfully"}
        except Exception as e:
            return {"success": False, "error": f"Failed to clean build: {e}"}

    def copy_dist_to_context(self, build_context_path: Path) -> Dict[str, Any]:
        """Copy built UI files to Docker build context."""
        if not self.is_ui_built():
            return {
                "success": False,
                "error": "UI not built - run build first",
                "recommendation": "Run with --rebuild-ui flag",
            }

        try:
            # Create static directory in build context
            static_dir = build_context_path / "static"
            static_dir.mkdir(parents=True, exist_ok=True)

            # Copy all dist files to static directory
            for item in self.dist_dir.iterdir():
                if item.is_file():
                    shutil.copy2(item, static_dir / item.name)
                elif item.is_dir():
                    shutil.copytree(item, static_dir / item.name, dirs_exist_ok=True)

            logger.info(f"Copied UI files to {static_dir}")

            return {
                "success": True,
                "static_dir": str(static_dir),
                "files_copied": len(list(self.dist_dir.iterdir())),
                "message": "UI files copied to build context",
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to copy UI files: {e}"}

    def get_build_info(self) -> Dict[str, Any]:
        """Get information about the current UI build."""
        if not self.is_ui_built():
            return {"built": False, "message": "UI not built"}

        try:
            dist_size = self._get_directory_size(self.dist_dir)
            file_count = len(list(self.dist_dir.rglob("*")))

            # Get package.json info
            package_info = {}
            if self.package_json.exists():
                import json

                with open(self.package_json) as f:
                    pkg_data = json.load(f)
                    package_info = {
                        "name": pkg_data.get("name", "unknown"),
                        "version": pkg_data.get("version", "unknown"),
                        "dependencies": len(pkg_data.get("dependencies", {})),
                    }

            return {
                "built": True,
                "dist_dir": str(self.dist_dir),
                "size_mb": round(dist_size / 1024 / 1024, 2),
                "file_count": file_count,
                "package_info": package_info,
                "message": "UI build available",
            }

        except Exception as e:
            return {"built": False, "error": f"Failed to get build info: {e}"}

    def _get_directory_size(self, path: Path) -> int:
        """Get total size of directory in bytes."""
        total_size = 0
        try:
            for item in path.rglob("*"):
                if item.is_file():
                    total_size += item.stat().st_size
        except Exception:
            pass
        return total_size

    @staticmethod
    def check_prerequisites() -> Dict[str, Any]:
        """Check if Node.js and npm are available."""
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

            return {
                "success": True,
                "node_version": node_result.stdout.strip(),
                "npm_version": npm_result.stdout.strip(),
                "message": "Prerequisites satisfied",
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
