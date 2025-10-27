"""Python runtime and dependency bundler for desktop packaging."""

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict


class PythonBundler:
    """Handles bundling Python runtime and dependencies for desktop apps."""

    def __init__(self) -> None:
        """Initialize the PythonBundler."""
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}"

    def bundle_runtime(
        self, agent_path: Path, tauri_path: Path, verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Bundle Python runtime and all dependencies.

        Args:
            agent_path: Path to the agent directory
            tauri_path: Path to the Tauri project
            verbose: Enable verbose logging

        Returns:
            Dict with success status
        """
        try:
            # Create python-runtime directory in Tauri resources
            runtime_dir = tauri_path / "src-tauri" / "resources" / "python-runtime"
            runtime_dir.mkdir(parents=True, exist_ok=True)

            # For now, we'll use the system Python and bundle dependencies with uv
            # In production, we'd download python-build-standalone, but that's complex
            # This is a simpler approach that still creates a functional bundle

            if verbose:
                print(f"  Using Python {self.python_version} from system")

            # Copy agent code
            if verbose:
                print("  Copying agent code...")
            agent_dest = runtime_dir / "agent"
            if agent_dest.exists():
                shutil.rmtree(agent_dest)
            shutil.copytree(
                agent_path,
                agent_dest,
                ignore=shutil.ignore_patterns(
                    ".git",
                    ".any_agent",
                    "__pycache__",
                    "*.pyc",
                    ".pytest_cache",
                    "venv",
                    ".venv",
                    "node_modules",
                ),
            )

            # Copy any_agent framework
            if verbose:
                print("  Copying any_agent framework...")
            any_agent_source = Path(__file__).parent.parent
            any_agent_dest = runtime_dir / "any_agent"
            if any_agent_dest.exists():
                shutil.rmtree(any_agent_dest)
            shutil.copytree(
                any_agent_source,
                any_agent_dest,
                ignore=shutil.ignore_patterns(
                    "__pycache__",
                    "*.pyc",
                    ".pytest_cache",
                    "tests",
                    "ui/node_modules",
                    "ui/dist",
                ),
            )

            # Create virtual environment using uv
            if verbose:
                print("  Creating Python virtual environment with uv...")

            venv_path = runtime_dir / "venv"

            # Create venv using uv
            result = subprocess.run(
                ["uv", "venv", str(venv_path)],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to create venv: {result.stderr}",
                }

            # Install any_agent dependencies
            if verbose:
                print("  Installing any_agent dependencies...")

            # Get the pyproject.toml from any_agent root
            project_root = Path(__file__).parent.parent.parent.parent
            pyproject_path = project_root / "pyproject.toml"

            if pyproject_path.exists():
                # Install from pyproject.toml
                result = subprocess.run(
                    [
                        "uv",
                        "pip",
                        "install",
                        "--python",
                        str(venv_path / "bin" / "python"),
                        "-e",
                        str(project_root),
                    ],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    return {
                        "success": False,
                        "error": f"Failed to install any_agent dependencies: {result.stderr}",
                    }

            # Install agent-specific dependencies
            agent_requirements = agent_path / "requirements.txt"
            agent_pyproject = agent_path / "pyproject.toml"

            if agent_requirements.exists():
                if verbose:
                    print("  Installing agent dependencies from requirements.txt...")
                result = subprocess.run(
                    [
                        "uv",
                        "pip",
                        "install",
                        "--python",
                        str(venv_path / "bin" / "python"),
                        "-r",
                        str(agent_requirements),
                    ],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    return {
                        "success": False,
                        "error": f"Failed to install agent requirements: {result.stderr}",
                    }
            elif agent_pyproject.exists():
                if verbose:
                    print("  Installing agent dependencies from pyproject.toml...")
                result = subprocess.run(
                    [
                        "uv",
                        "pip",
                        "install",
                        "--python",
                        str(venv_path / "bin" / "python"),
                        "-e",
                        str(agent_path),
                    ],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    return {
                        "success": False,
                        "error": f"Failed to install agent from pyproject.toml: {result.stderr}",
                    }

            # Create activation script
            activate_script = runtime_dir / "activate.sh"
            with open(activate_script, "w") as f:
                f.write(f"""#!/bin/bash
# Activate Python virtual environment
source "{venv_path}/bin/activate"
""")
            activate_script.chmod(0o755)

            return {"success": True, "runtime_dir": str(runtime_dir)}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_python_executable(self, runtime_dir: Path) -> Path:
        """
        Get path to Python executable in bundled runtime.

        Args:
            runtime_dir: Path to the runtime directory

        Returns:
            Path to Python executable
        """
        return runtime_dir / "venv" / "bin" / "python"
