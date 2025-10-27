"""macOS desktop application packager using Tauri."""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

import click


class MacAppPackager:
    """Packages any-agent agents into macOS desktop applications using Tauri."""

    def __init__(self) -> None:
        """Initialize the MacAppPackager."""
        self.default_icon_path = None  # Will be set to generic icon path

    def package(
        self,
        agent_path: Path,
        test_mode: bool = False,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """
        Package an agent into a macOS desktop application.

        Args:
            agent_path: Path to the agent directory
            test_mode: If True, run app locally without building installer
            verbose: Enable verbose logging

        Returns:
            Dict with success status and relevant paths or error messages
        """
        try:
            # 1. Check prerequisites
            prereq_result = self._check_prerequisites()
            if not prereq_result["success"]:
                return prereq_result

            # 2. Check for existing build and prompt
            any_agent_dir = agent_path / ".any_agent"
            if any_agent_dir.exists():
                rebuild = click.confirm(
                    f"\n.any_agent directory already exists. Rebuild from scratch?",
                    default=True,
                )
                if rebuild:
                    if verbose:
                        click.echo("🗑️  Removing existing .any_agent directory...")
                    shutil.rmtree(any_agent_dir)

            # 3. Collect metadata interactively
            if verbose:
                click.echo("\n📝 Collecting application metadata...")
            metadata = self._collect_metadata(agent_path)

            # 4. Detect framework
            if verbose:
                click.echo("\n🔍 Detecting agent framework...")
            framework_result = self._detect_framework(agent_path)
            if not framework_result["success"]:
                return framework_result

            # 5. Create Tauri project structure
            if verbose:
                click.echo("\n🏗️  Creating Tauri project structure...")
            tauri_result = self._create_tauri_project(
                agent_path, metadata, framework_result
            )
            if not tauri_result["success"]:
                return tauri_result

            # 6. Bundle Python runtime and dependencies
            if verbose:
                click.echo("\n🐍 Bundling Python runtime and dependencies...")
            python_result = self._bundle_python_runtime(
                agent_path, tauri_result["tauri_path"]
            )
            if not python_result["success"]:
                return python_result

            # 7. Generate run_agent.py entrypoint
            if verbose:
                click.echo("\n📜 Generating custom entrypoint script...")
            entrypoint_result = self._generate_entrypoint(
                agent_path, tauri_result["tauri_path"], framework_result
            )
            if not entrypoint_result["success"]:
                return entrypoint_result

            # 8. Build or test
            if test_mode:
                if verbose:
                    click.echo("\n🧪 Running packaged app in test mode...")
                return self._test_package(tauri_result["tauri_path"], verbose)
            else:
                if verbose:
                    click.echo("\n🔨 Building macOS installer...")
                return self._build_package(tauri_result["tauri_path"], verbose)

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _check_prerequisites(self) -> Dict[str, Any]:
        """
        Check that all required tools are installed.

        Returns:
            Dict with success status and error/recommendation if failed
        """
        prerequisites = {
            "node": {"cmd": ["node", "--version"], "name": "Node.js"},
            "npm": {"cmd": ["npm", "--version"], "name": "npm"},
            "rustc": {"cmd": ["rustc", "--version"], "name": "Rust"},
            "cargo": {"cmd": ["cargo", "--version"], "name": "Cargo"},
        }

        missing = []
        for key, prereq in prerequisites.items():
            try:
                subprocess.run(
                    prereq["cmd"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing.append(prereq["name"])

        if missing:
            error_msg = f"Missing prerequisites: {', '.join(missing)}"
            recommendations = {
                "Node.js": "Install from https://nodejs.org/ or use: brew install node",
                "npm": "Comes with Node.js installation",
                "Rust": "Install from https://rustup.rs/ or use: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh",
                "Cargo": "Comes with Rust installation",
            }

            recommendation = "\n".join(
                [f"  • {name}: {rec}" for name, rec in recommendations.items() if name in missing]
            )

            return {
                "success": False,
                "error": error_msg,
                "recommendation": f"Installation instructions:\n{recommendation}",
            }

        # Check for Tauri CLI
        try:
            result = subprocess.run(
                ["cargo", "install", "--list"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            if "tauri-cli" not in result.stdout:
                return {
                    "success": False,
                    "error": "Tauri CLI not installed",
                    "recommendation": "Install Tauri CLI: cargo install tauri-cli",
                }
        except subprocess.CalledProcessError:
            return {
                "success": False,
                "error": "Could not check for Tauri CLI",
                "recommendation": "Ensure Cargo is working properly",
            }

        # Check for Xcode Command Line Tools on macOS
        try:
            subprocess.run(
                ["xcode-select", "-p"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {
                "success": False,
                "error": "Xcode Command Line Tools not installed",
                "recommendation": "Install with: xcode-select --install",
            }

        return {"success": True}

    def _collect_metadata(self, agent_path: Path) -> Dict[str, str]:
        """
        Collect application metadata interactively.

        Args:
            agent_path: Path to the agent directory

        Returns:
            Dict with collected metadata
        """
        # Check for existing manifest
        manifest_path = agent_path / ".any_agent" / "package-manifest.json"
        if manifest_path.exists():
            with open(manifest_path, "r") as f:
                existing = json.load(f)
            click.echo("\nFound existing package manifest:")
            for key, value in existing.items():
                if key != "timestamp":
                    click.echo(f"  {key}: {value}")

            if click.confirm("\nUse these values?", default=True):
                return existing

        # Prompt for metadata
        click.echo("\n" + "=" * 50)
        click.echo("Desktop Application Configuration")
        click.echo("=" * 50)

        app_name = click.prompt("\n📱 Application name", default=agent_path.name.replace("_", " ").title())
        version = click.prompt("🔢 Version", default="1.0.0")
        author = click.prompt("👤 Author name", default="")
        description = click.prompt("📝 Description", default=f"AI agent powered by {agent_path.name}")

        # Icon path (optional)
        icon_path = click.prompt(
            "🎨 Icon file path (press Enter for default)",
            default="",
            show_default=False,
        )

        if icon_path and not Path(icon_path).exists():
            click.echo(f"⚠️  Icon file not found: {icon_path}")
            click.echo("   Using default icon instead")
            icon_path = ""

        metadata = {
            "app_name": app_name,
            "version": version,
            "author": author,
            "description": description,
            "icon_path": icon_path or "default",
        }

        return metadata

    def _detect_framework(self, agent_path: Path) -> Dict[str, Any]:
        """
        Detect the agent's framework.

        Args:
            agent_path: Path to the agent directory

        Returns:
            Dict with success status and framework information
        """
        try:
            from ..core.docker_orchestrator import AgentOrchestrator

            orchestrator = AgentOrchestrator()
            adapter = orchestrator.detect_framework(agent_path)

            if not adapter:
                return {
                    "success": False,
                    "error": "Could not detect agent framework",
                }

            framework_name = adapter.__class__.__name__.replace("Adapter", "")

            return {
                "success": True,
                "adapter": adapter,
                "framework_name": framework_name,
            }

        except Exception as e:
            return {"success": False, "error": f"Framework detection failed: {e}"}

    def _create_tauri_project(
        self,
        agent_path: Path,
        metadata: Dict[str, str],
        framework_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create the Tauri project structure.

        Args:
            agent_path: Path to the agent directory
            metadata: Application metadata
            framework_result: Framework detection result

        Returns:
            Dict with success status and tauri project path
        """
        from .tauri_generator import TauriProjectGenerator

        # Create .any_agent/tauri-app directory
        tauri_path = agent_path / ".any_agent" / "tauri-app"
        tauri_path.mkdir(parents=True, exist_ok=True)

        # Save manifest
        manifest_path = agent_path / ".any_agent" / "package-manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(metadata, f, indent=2)

        # Generate Tauri project
        generator = TauriProjectGenerator()
        result = generator.generate_project(tauri_path, metadata, agent_path)

        if not result["success"]:
            return result

        return {
            "success": True,
            "tauri_path": tauri_path,
        }

    def _bundle_python_runtime(
        self, agent_path: Path, tauri_path: Path
    ) -> Dict[str, Any]:
        """
        Bundle Python runtime and dependencies.

        Args:
            agent_path: Path to the agent directory
            tauri_path: Path to the Tauri project

        Returns:
            Dict with success status
        """
        # TODO: Implement Python runtime bundling
        # This is a placeholder - will be implemented in next steps

        return {"success": True}

    def _generate_entrypoint(
        self,
        agent_path: Path,
        tauri_path: Path,
        framework_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate the custom run_agent.py entrypoint script.

        Args:
            agent_path: Path to the agent directory
            tauri_path: Path to the Tauri project
            framework_result: Framework detection result

        Returns:
            Dict with success status
        """
        # TODO: Implement entrypoint generation
        # This is a placeholder - will be implemented in next steps

        return {"success": True}

    def _test_package(self, tauri_path: Path, verbose: bool) -> Dict[str, Any]:
        """
        Run the packaged app in test mode without building installer.

        Args:
            tauri_path: Path to the Tauri project
            verbose: Enable verbose output

        Returns:
            Dict with success status and app path
        """
        # TODO: Implement test mode
        # This is a placeholder - will be implemented in next steps

        return {
            "success": True,
            "app_path": str(tauri_path),
        }

    def _build_package(self, tauri_path: Path, verbose: bool) -> Dict[str, Any]:
        """
        Build the macOS installer (.dmg).

        Args:
            tauri_path: Path to the Tauri project
            verbose: Enable verbose output

        Returns:
            Dict with success status and dmg path
        """
        # TODO: Implement full build
        # This is a placeholder - will be implemented in next steps

        return {
            "success": True,
            "dmg_path": str(tauri_path / "target" / "release" / "bundle" / "dmg"),
        }
