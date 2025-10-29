"""Agent bundler using PyInstaller for creating standalone executables."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from any_agent.core.framework_detector import FrameworkDetector
from any_agent.shared.entrypoint_templates import (
    UnifiedEntrypointGenerator,
    EntrypointContext,
)


class AgentBundler:
    """Bundles Python agents into standalone executables using PyInstaller."""

    def __init__(self, agent_path: Path) -> None:
        """
        Initialize the AgentBundler.

        Args:
            agent_path: Path to the agent directory
        """
        self.agent_path = agent_path.resolve()
        self.detector = FrameworkDetector()
        self.entrypoint_generator = UnifiedEntrypointGenerator()

    def bundle_agent(
        self,
        output_dir: Path,
        app_name: str,
        framework: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Bundle agent into a standalone executable.

        Args:
            output_dir: Directory where bundled executable will be created
            app_name: Name for the executable
            framework: Framework type string (auto-detected if None)

        Returns:
            Dict with success status and executable path
        """
        try:
            # Detect framework if not provided
            if framework is None:
                adapter = self.detector.detect_framework(self.agent_path)
                if adapter is None:
                    raise ValueError(f"Could not detect framework in {self.agent_path}")
                framework = adapter.framework_name

            # Create PyInstaller spec file
            spec_file = self._create_pyinstaller_spec(
                output_dir, app_name, framework
            )

            # Run PyInstaller
            executable_path = self._run_pyinstaller(spec_file, output_dir)

            return {
                "success": True,
                "executable_path": str(executable_path),
                "framework": framework,
            }

        except Exception as bundle_error:
            return {
                "success": False,
                "error": str(bundle_error),
            }

    def _create_pyinstaller_spec(
        self,
        output_dir: Path,
        app_name: str,
        framework: str,
    ) -> Path:
        """
        Create PyInstaller spec file for the agent.

        Args:
            output_dir: Output directory for the spec file
            app_name: Name for the application
            framework: Framework type

        Returns:
            Path to the created spec file
        """
        # Generate A2A entrypoint for the agent
        entry_point = self._generate_a2a_entrypoint(output_dir, framework)

        # Collect framework-specific hidden imports and data files
        hidden_imports = self._get_hidden_imports(framework)
        datas = self._get_data_files(framework)

        # Create spec file content
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

# PyInstaller spec file for {app_name}
# Framework: {framework}

import sys
from pathlib import Path

block_cipher = None

# Agent source directory
agent_path = Path(r"{self.agent_path}")

# Collect all Python files from agent directory
agent_files = []
for py_file in agent_path.rglob("*.py"):
    if "__pycache__" not in str(py_file):
        agent_files.append((str(py_file), str(py_file.parent.relative_to(agent_path.parent))))

a = Analysis(
    [r"{entry_point}"],
    pathex=[r"{self.agent_path.parent}"],
    binaries=[],
    datas=agent_files + {datas},
    hiddenimports={hidden_imports},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{app_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''

        spec_file = output_dir / f"{app_name}.spec"
        spec_file.parent.mkdir(parents=True, exist_ok=True)

        with open(spec_file, "w") as f:
            f.write(spec_content)

        return spec_file

    def _generate_a2a_entrypoint(
        self, output_dir: Path, framework: str, port: int = 8035
    ) -> Path:
        """
        Generate an A2A server entrypoint for the agent.

        Args:
            output_dir: Directory where entrypoint will be created
            framework: Framework type string
            port: Port for A2A server (default: 8035 for Google ADK)

        Returns:
            Path to the generated entrypoint file
        """
        # Map framework names to entrypoint generator format
        framework_map = {
            "GoogleADK": "google_adk",
            "AWSStrands": "aws_strands",
            "LangChain": "langchain",
            "LangGraph": "langgraph",
            "CrewAI": "crewai",
        }

        # Normalize framework name
        framework_key = framework_map.get(framework, framework.lower())

        # Set framework-specific default ports
        port_map = {
            "google_adk": 8035,
            "aws_strands": 8045,
            "langchain": 8055,
            "langgraph": 8065,
            "crewai": 8075,
        }
        port = port_map.get(framework_key, 8080)

        # Generate A2A entrypoint using the unified generator
        context = EntrypointContext(
            agent_name=self.agent_path.name,
            agent_path=self.agent_path,
            framework=framework_key,
            port=port,
            add_ui=False,  # No UI for sidecar
            deployment_type="sidecar",  # Custom deployment type for bundling
        )

        entrypoint_content = self.entrypoint_generator.generate_entrypoint(context)

        # Add uvicorn launcher at the end for standalone execution
        uvicorn_launcher = f'''

if __name__ == "__main__":
    import uvicorn
    import sys

    # Parse port from command line or use default
    port = {port}
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {{sys.argv[1]}}, using default: {port}")

    # Start uvicorn server
    print(f"Starting A2A server on port {{port}}...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
'''

        full_entrypoint = entrypoint_content + uvicorn_launcher

        # Save entrypoint in the agent directory (accessible to PyInstaller)
        # Create a temp directory for build artifacts
        temp_build_dir = self.agent_path / ".any_agent_build"
        temp_build_dir.mkdir(parents=True, exist_ok=True)

        entrypoint_file = temp_build_dir / "a2a_entrypoint.py"
        with open(entrypoint_file, "w") as f:
            f.write(full_entrypoint)

        # Return absolute path
        return entrypoint_file.resolve()

    def _get_hidden_imports(self, framework: str) -> List[str]:
        """
        Get list of hidden imports needed for PyInstaller.

        Args:
            framework: Framework type string

        Returns:
            List of module names to include as hidden imports
        """
        common_imports = [
            "asyncio",
            "json",
            "typing",
            "pathlib",
        ]

        # Normalize framework name for comparison
        framework_key = framework.lower().replace("_", "").replace("-", "") if framework else ""

        framework_imports = {
            "googleadk": [
                "google",
                "google.genai",
                "google.genai.types",
                "google.api_core",
                "google.auth",
                "google.adk",
                "google.adk.a2a",
                "google.adk.a2a.utils",
                "google.adk.a2a.utils.agent_to_a2a",
                "aiohttp",
                "fastapi",
                "starlette",
                "starlette.responses",
                "starlette.routing",
                "uvicorn",
                "uvicorn.logging",
                "uvicorn.protocols",
                "pydantic",
                "a2a",
                "a2a.server",
            ],
            "adk": [
                "google",
                "google.genai",
                "google.genai.types",
                "google.api_core",
                "google.auth",
                "google.adk",
                "google.adk.a2a",
                "google.adk.a2a.utils",
                "google.adk.a2a.utils.agent_to_a2a",
                "aiohttp",
                "fastapi",
                "starlette",
                "starlette.responses",
                "starlette.routing",
                "uvicorn",
                "uvicorn.logging",
                "uvicorn.protocols",
                "pydantic",
                "a2a",
                "a2a.server",
            ],
            "awsstrands": [
                "anthropic",
                "boto3",
                "botocore",
                "fastapi",
                "uvicorn",
                "pydantic",
            ],
            "strands": [
                "anthropic",
                "boto3",
                "botocore",
                "fastapi",
                "uvicorn",
                "pydantic",
            ],
            "langchain": [
                "langchain",
                "langchain_core",
                "langchain_openai",
                "openai",
                "fastapi",
                "uvicorn",
            ],
            "langgraph": [
                "langgraph",
                "langchain",
                "langchain_core",
                "fastapi",
                "uvicorn",
            ],
            "crewai": [
                "crewai",
                "langchain",
                "openai",
                "fastapi",
                "uvicorn",
            ],
        }

        return common_imports + framework_imports.get(framework_key, [])

    def _get_data_files(self, framework: str) -> List[tuple]:
        """
        Get list of data files to include in the bundle.

        Args:
            framework: Framework type string

        Returns:
            List of (source, dest) tuples for data files
        """
        data_files = []

        # Include common config files
        for pattern in ["*.yaml", "*.yml", "*.json", "*.env.example"]:
            for config_file in self.agent_path.glob(pattern):
                if config_file.name != ".env":  # Never include .env
                    data_files.append(
                        (str(config_file), str(config_file.relative_to(self.agent_path.parent)))
                    )

        # Framework-specific data files
        framework_normalized = framework.lower().replace("_", "").replace("-", "")
        if framework_normalized in ("googleadk", "adk"):
            # Include ADK config files
            for adk_file in self.agent_path.rglob("*.adk"):
                data_files.append(
                    (str(adk_file), str(adk_file.relative_to(self.agent_path.parent)))
                )

        return data_files

    def _run_pyinstaller(self, spec_file: Path, output_dir: Path) -> Path:
        """
        Run PyInstaller to create the executable.

        Args:
            spec_file: Path to the PyInstaller spec file
            output_dir: Output directory for the executable

        Returns:
            Path to the created executable

        Raises:
            subprocess.CalledProcessError: If PyInstaller fails
        """
        # Ensure PyInstaller is available
        try:
            subprocess.run(
                ["uv", "pip", "show", "pyinstaller"],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            # Install PyInstaller if not available
            subprocess.run(
                ["uv", "pip", "install", "pyinstaller"],
                check=True,
            )

        # Run PyInstaller
        dist_dir = output_dir / "dist"
        work_dir = output_dir / "build"

        # Use absolute paths to avoid cwd issues
        abs_spec_file = spec_file.resolve()
        abs_dist_dir = dist_dir.resolve()
        abs_work_dir = work_dir.resolve()

        subprocess.run(
            [
                sys.executable,
                "-m",
                "PyInstaller",
                str(abs_spec_file),
                "--distpath",
                str(abs_dist_dir),
                "--workpath",
                str(abs_work_dir),
                "--noconfirm",
            ],
            check=True,
            cwd=self.agent_path,
        )

        # Find the created executable
        app_name = spec_file.stem
        executable = dist_dir / app_name

        if not executable.exists():
            raise FileNotFoundError(
                f"PyInstaller completed but executable not found at {executable}"
            )

        return executable

    def create_wrapper_script(
        self,
        executable_path: Path,
        wrapper_path: Path,
        port: int = 8080,
    ) -> None:
        """
        Create a wrapper script that starts the agent with proper environment.

        Args:
            executable_path: Path to the bundled executable
            wrapper_path: Path where wrapper script will be created
            port: Port for the agent to listen on
        """
        wrapper_content = f'''#!/bin/bash
# Wrapper script for {executable_path.name}

# Set environment variables
export PORT={port}
export HOST=0.0.0.0

# Run the agent executable
exec "{executable_path}" "$@"
'''

        wrapper_path.parent.mkdir(parents=True, exist_ok=True)
        with open(wrapper_path, "w") as f:
            f.write(wrapper_content)

        # Make executable
        wrapper_path.chmod(0o755)
