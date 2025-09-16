"""Dependency installer for Any Agent framework."""

import logging
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class DependencyInstaller:
    """Handles installation of agent dependencies."""

    def __init__(self):
        """Initialize dependency installer."""
        pass

    def install_agent_dependencies(self, agent_path: Path) -> bool:
        """
        Install dependencies for an agent by checking for requirements files.

        Args:
            agent_path: Path to the agent directory

        Returns:
            True if installation succeeded or no dependencies found, False if failed
        """
        try:
            # Look for requirements files
            requirements_files = self._find_requirements_files(agent_path)

            if not requirements_files:
                logger.debug(f"No requirements files found in {agent_path}")
                return True

            # Install each requirements file
            for req_file in requirements_files:
                if not self._install_requirements_file(req_file):
                    return False

            return True

        except Exception as e:
            logger.error(f"Error installing dependencies for {agent_path}: {e}")
            return False

    def _find_requirements_files(self, agent_path: Path) -> List[Path]:
        """Find requirements files in the agent directory."""
        requirements_files = []

        # Check for various requirements file patterns
        patterns = [
            "requirements.txt",
            "requirements-dev.txt",
            "requirements-local.txt",
            "pyproject.toml"
        ]

        for pattern in patterns:
            req_file = agent_path / pattern
            if req_file.exists():
                requirements_files.append(req_file)
                logger.info(f"Found requirements file: {req_file}")

        return requirements_files

    def _install_requirements_file(self, req_file: Path) -> bool:
        """Install dependencies from a requirements file."""
        try:
            if req_file.name == "pyproject.toml":
                return self._install_pyproject_toml(req_file)
            else:
                return self._install_requirements_txt(req_file)

        except Exception as e:
            logger.error(f"Failed to install {req_file}: {e}")
            return False

    def _install_requirements_txt(self, req_file: Path) -> bool:
        """Install dependencies from requirements.txt using uv."""
        try:
            logger.info(f"Installing dependencies from {req_file}")

            # Use uv add to install requirements
            cmd = ["uv", "add", "--requirements", str(req_file)]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            logger.info(f"Successfully installed dependencies from {req_file}")
            if result.stdout:
                logger.debug(f"uv output: {result.stdout}")

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install {req_file}: {e}")
            if e.stderr:
                logger.error(f"uv error: {e.stderr}")
            return False
        except FileNotFoundError:
            logger.error("uv not found. Please ensure uv is installed.")
            return False

    def _install_pyproject_toml(self, req_file: Path) -> bool:
        """Install dependencies from pyproject.toml using uv."""
        try:
            logger.info(f"Installing dependencies from {req_file}")

            # Change to the directory containing pyproject.toml
            original_cwd = Path.cwd()
            req_dir = req_file.parent

            try:
                import os
                os.chdir(req_dir)

                # Use uv sync to install from pyproject.toml
                cmd = ["uv", "sync"]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )

                logger.info(f"Successfully installed dependencies from {req_file}")
                if result.stdout:
                    logger.debug(f"uv output: {result.stdout}")

                return True

            finally:
                os.chdir(original_cwd)

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install {req_file}: {e}")
            if e.stderr:
                logger.error(f"uv error: {e.stderr}")
            return False
        except FileNotFoundError:
            logger.error("uv not found. Please ensure uv is installed.")
            return False

    def check_dependency_availability(self, dependency: str) -> bool:
        """Check if a Python dependency is available for import."""
        try:
            __import__(dependency)
            return True
        except ImportError:
            return False