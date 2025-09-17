"""Unified Docker container generation for all agent frameworks."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from ..adapters.base import AgentMetadata
from ..shared.entrypoint_templates import UnifiedEntrypointGenerator, EntrypointContext
from ..shared.chat_endpoints_generator import ChatEndpointsGenerator
from ..shared.url_utils import localhost_urls

logger = logging.getLogger(__name__)


class UnifiedDockerfileGenerator:
    """Generate Dockerfile for any agent framework using unified approach."""

    def __init__(self):
        self.base_image = "python:3.11-slim"
        self.entrypoint_generator = UnifiedEntrypointGenerator()
        self.chat_endpoints_generator = ChatEndpointsGenerator()

        # Package manager configurations by distribution type
        self.package_managers = {
            "apt": {
                "update_cmd": "apt-get update",
                "install_cmd": "apt-get install -y",
                "packages": ["gcc", "g++", "curl"],
                "cleanup_cmd": "rm -rf /var/lib/apt/lists/*",
            },
            "apk": {
                "update_cmd": None,  # apk doesn't need separate update
                "install_cmd": "apk add --no-cache",
                "packages": ["gcc", "g++", "curl", "musl-dev"],
                "cleanup_cmd": None,  # apk doesn't need cleanup
            },
            "yum": {
                "update_cmd": None,  # yum update is optional
                "install_cmd": "yum install -y",
                "packages": ["gcc", "gcc-c++", "curl"],
                "cleanup_cmd": "yum clean all",
            },
            "dnf": {
                "update_cmd": None,  # dnf update is optional
                "install_cmd": "dnf install -y",
                "packages": ["gcc", "gcc-c++", "curl"],
                "cleanup_cmd": "dnf clean all",
            },
        }

        # Framework-specific configurations
        self.framework_configs = {
            "google_adk": {
                "default_port": 8035,
                "env_vars": {
                    "GOOGLE_MODEL": "gemini-2.0-flash",
                    "GOOGLE_API_KEY": "",
                },
                "dependencies": [
                    "google-adk[a2a]",  # Framework-specific A2A support
                    "uvicorn[standard]",  # ASGI server for A2A protocol
                    "a2a-sdk>=0.1.0",  # Universal A2A client
                ],
                "entrypoint_script": "_adk_entrypoint.py",
                "server_type": "google_adk_a2a",
            },
            "aws_strands": {
                "default_port": 8045,
                "env_vars": {
                    "ANTHROPIC_API_KEY": "",
                },
                "dependencies": [
                    "strands-agents[a2a]",  # Framework-specific A2A support
                    "uvicorn[standard]",  # ASGI server for A2A protocol
                    "fastapi",  # Required by Strands A2A implementation
                    "a2a-sdk>=0.1.0",  # Universal A2A client
                    "anthropic>=0.37.0",  # Anthropic API client for direct API usage
                ],
                "entrypoint_script": "_strands_entrypoint.py",
                "server_type": "strands_a2a",
            },
            "langchain": {
                "default_port": 8055,
                "env_vars": {
                    "OPENAI_API_KEY": "",
                },
                "dependencies": [
                    "uvicorn[standard]",  # ASGI server for A2A protocol
                    "fastapi",  # Required for A2A implementation
                    "a2a-sdk>=0.1.0",  # Universal A2A client
                ],
                "entrypoint_script": "_generic_entrypoint.py",
                "server_type": "generic_a2a",
            },
            "langgraph": {
                "default_port": 8065,
                "env_vars": {
                    "OPENAI_API_KEY": "",
                },
                "dependencies": [
                    "uvicorn[standard]",  # ASGI server for A2A protocol
                    "fastapi",  # Required for A2A implementation
                    "a2a-sdk>=0.1.0",  # Universal A2A client
                ],
                "entrypoint_script": "_generic_entrypoint.py",
                "server_type": "generic_a2a",
            },
            "crewai": {
                "default_port": 8075,
                "env_vars": {
                    "OPENAI_API_KEY": "",
                },
                "dependencies": [
                    "crewai",
                    "uvicorn[standard]",
                    "fastapi",
                    "a2a-sdk>=0.1.0",
                ],
                "entrypoint_script": "_generic_entrypoint.py",
                "server_type": "generic_a2a",
            },
        }

    def get_framework_config(self, framework: str) -> Dict:
        """Get configuration for a specific framework."""
        config = self.framework_configs.get(framework)
        if not config:
            # Default configuration for unknown frameworks
            config = {
                "default_port": 8085,
                "env_vars": {},
                "dependencies": [
                    "uvicorn[standard]",
                    "fastapi",
                    "a2a-sdk>=0.1.0",
                ],
                "entrypoint_script": "_generic_entrypoint.py",
                "server_type": "generic_a2a",
            }
            logger.warning(
                f"Unknown framework '{framework}', using default configuration"
            )
        return config

    def _is_standard_python_base(self, base_image: str) -> bool:
        """Check if this is a standard Python base image we can optimize for."""
        base_image_lower = base_image.lower()
        return base_image_lower.startswith("python:") or base_image_lower.startswith(
            "python3:"
        )

    def detect_base_image_type(self, base_image: str) -> str:
        """
        Detect package manager type based on base image name.

        Args:
            base_image: Docker base image name (e.g., "python:3.11-alpine")

        Returns:
            Package manager type: 'apt', 'apk', 'yum', 'dnf', or 'unknown'
        """
        base_image_lower = base_image.lower()

        # Alpine-based images
        if any(keyword in base_image_lower for keyword in ["alpine", "apk"]):
            return "apk"

        # Red Hat family (CentOS, RHEL, Fedora)
        elif any(
            keyword in base_image_lower
            for keyword in ["centos", "rhel", "rocky", "almalinux"]
        ):
            return "yum"
        elif any(keyword in base_image_lower for keyword in ["fedora"]):
            return "dnf"

        # Debian/Ubuntu family (includes python:* images which are Debian-based)
        elif any(
            keyword in base_image_lower
            for keyword in ["ubuntu", "debian", "python", "node"]
        ):
            return "apt"

        # Amazon Linux (uses yum)
        elif "amazonlinux" in base_image_lower:
            return "yum"

        # OpenSUSE (uses zypper, but we'll fallback to yum for now)
        elif any(keyword in base_image_lower for keyword in ["opensuse", "suse"]):
            return "yum"

        # Unknown/custom images - skip system package installation
        else:
            logger.info(
                f"Unknown base image type: {base_image}. Skipping system package installation."
            )
            return "unknown"

    def generate_system_dependencies_section(self, base_image: str) -> str:
        """
        Generate the system dependencies installation section based on base image type.

        Args:
            base_image: Docker base image name

        Returns:
            Dockerfile section for installing system dependencies
        """
        pkg_manager_type = self.detect_base_image_type(base_image)

        if pkg_manager_type == "unknown":
            return "# Skipping system dependencies - unknown base image type\n"

        config = self.package_managers[pkg_manager_type]

        # Build the RUN command
        commands = []

        if config["update_cmd"]:
            commands.append(config["update_cmd"])

        install_cmd = f"{config['install_cmd']} {' '.join(config['packages'])}"
        commands.append(install_cmd)

        if config["cleanup_cmd"]:
            commands.append(config["cleanup_cmd"])

        # Join commands with && and proper line continuation
        if len(commands) == 1:
            run_command = f"RUN {commands[0]}"
        else:
            formatted_commands = []
            for i, cmd in enumerate(commands):
                if i == 0:
                    formatted_commands.append(f"RUN {cmd}")
                elif i == len(commands) - 1:
                    formatted_commands.append(f"    && {cmd}")
                else:
                    formatted_commands.append(f"    && {cmd}")

            run_command = " \\\n".join(formatted_commands)

        return f"""# Install system dependencies including uv
{run_command}
"""

    def _generate_python_validation_section(self, base_image: str) -> str:
        """Generate Python validation section for custom base images."""
        is_standard = self._is_standard_python_base(base_image)

        if not is_standard:
            # Add Python validation for custom base images
            return """# Validate Python and pip are available in custom base image
RUN python3 --version || python --version || (echo "❌ ERROR: Python not found in base image '{}'. Please use a base image with Python installed." && exit 1)
RUN pip3 --version || pip --version || (echo "❌ ERROR: pip not found in base image '{}'. Please use a base image with pip installed." && exit 1)

""".format(base_image, base_image)
        else:
            # Skip validation for standard Python base images
            return ""

    def _generate_package_installation_section(self, base_image: str) -> str:
        """
        Generate Python package installation section.

        Simplified approach: Use pip for all base images with proper user site configuration.
        This avoids complex base image detection and permission issues.
        """
        is_standard = self._is_standard_python_base(base_image)

        if is_standard:
            # For standard Python images, we can use system installation with uv
            return """# Install uv for faster Python package management
RUN pip install --no-cache-dir uv

# Copy requirements and install dependencies  
COPY requirements.txt ./
RUN uv pip install --system --no-cache -r requirements.txt
"""
        else:
            # For custom/unknown base images, use conservative pip approach
            return """# Install Python dependencies (conservative approach for custom base images)
COPY requirements.txt ./
RUN pip3 install --no-cache-dir --user -r requirements.txt || pip install --no-cache-dir --user -r requirements.txt

# Ensure user site packages are accessible
ENV PYTHONUSERBASE=/home/appuser/.local
ENV PATH="/home/appuser/.local/bin:$PATH"
"""

    def _generate_run_command(self, base_image: str, entrypoint_script: str) -> str:
        """Generate the appropriate run command."""
        is_standard = self._is_standard_python_base(base_image)
        entrypoint_module = entrypoint_script.replace(".py", "")

        if is_standard:
            # Use uv run for standard Python images
            return f'CMD ["sh", "-c", "uv run uvicorn {entrypoint_module}:app --host 0.0.0.0 --port $AGENT_PORT"]'
        else:
            # Use plain python for custom base images
            return f'CMD ["sh", "-c", "python -m uvicorn {entrypoint_module}:app --host 0.0.0.0 --port $AGENT_PORT"]'

    def generate_dockerfile(
        self,
        agent_path: Path,
        metadata: AgentMetadata,
        base_image: Optional[str] = None,
    ) -> str:
        """
        Generate Dockerfile content for any framework.

        Args:
            agent_path: Path to agent directory
            metadata: Agent metadata

        Returns:
            Dockerfile content as string
        """
        framework_config = self.get_framework_config(metadata.framework)
        port = framework_config["default_port"]
        env_vars = framework_config["env_vars"]

        # Use custom base image if provided, otherwise use default
        selected_base_image = base_image or self.base_image

        # Build environment variables section
        env_vars_section = f"# Set framework identifier for A2A client selection\nENV AGENT_FRAMEWORK={metadata.framework}\n\n"

        if env_vars:
            env_vars_section += f"# Set {metadata.framework.replace('_', ' ').title()} environment variables\n"
            for key, value in env_vars.items():
                env_vars_section += f'ENV {key}="{value}"\n'

        dockerfile_content = f"""# Generated Dockerfile for {metadata.name} ({metadata.framework.replace("_", " ").title()} Agent)
FROM {selected_base_image}

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

{self.generate_system_dependencies_section(selected_base_image)}
{self._generate_python_validation_section(selected_base_image)}
{self._generate_package_installation_section(selected_base_image)}

# Copy agent files
COPY . .

# Copy framework-specific entrypoint script
COPY {framework_config["entrypoint_script"]} .

# Set default port (can be overridden by environment variable)
ENV AGENT_PORT={port}

{env_vars_section}
# Expose main port
EXPOSE $AGENT_PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:$AGENT_PORT/health || exit 1

# Run the framework-specific server
{self._generate_run_command(selected_base_image, framework_config["entrypoint_script"])}
"""

        return dockerfile_content

    def generate_entrypoint(
        self, agent_path: Path, metadata: AgentMetadata, add_ui: bool = False
    ) -> str:
        """Generate framework-specific entrypoint script using shared templates."""
        framework_config = self.get_framework_config(metadata.framework)

        # Create EntrypointContext for shared generator
        context = EntrypointContext(
            agent_name=metadata.name,
            agent_path=agent_path,
            framework=metadata.framework,
            port=framework_config["default_port"],
            add_ui=add_ui,
            deployment_type="docker",
        )

        return self.entrypoint_generator.generate_entrypoint(context)

    def create_build_context(
        self,
        agent_path: Path,
        output_dir: Path,
        metadata: AgentMetadata,
        add_ui: bool = False,
        port: Optional[int] = None,
        base_image: Optional[str] = None,
    ) -> Path:
        """Create Docker build context with all necessary files."""
        framework_config = self.get_framework_config(metadata.framework)
        if port is None:
            port = framework_config["default_port"]

        build_context = output_dir / f"{metadata.name}-docker-context"
        build_context.mkdir(parents=True, exist_ok=True)

        # Copy agent files
        import shutil

        agent_package_dir = build_context / agent_path.name
        agent_package_dir.mkdir(parents=True, exist_ok=True)

        # Copy all files and directories from agent_path to agent_package_dir
        for item in agent_path.iterdir():
            if (
                item.name.startswith(".")
                or item.name in ["__pycache__", ".git", "tmp", "any_agent"]
                or item.name.endswith("-docker-context")
            ):
                continue

            if item.is_file():
                # Copy all files (not just .py files)
                shutil.copy2(item, agent_package_dir / item.name)
                logger.info(f"Copied file: {item.name}")
            elif item.is_dir():
                # Copy all directories
                shutil.copytree(item, agent_package_dir / item.name, dirs_exist_ok=True)
                logger.info(f"Copied directory: {item.name}")

        # Copy local dependencies
        if metadata.local_dependencies:
            logger.info(
                f"Copying {len(metadata.local_dependencies)} local dependencies"
            )
            for dep_path in metadata.local_dependencies:
                dep_dir = Path(dep_path)
                if dep_dir.exists() and dep_dir.is_dir():
                    dest_path = build_context / dep_dir.name
                    shutil.copytree(dep_dir, dest_path, dirs_exist_ok=True)
                    logger.info(f"Copied local dependency directory: {dep_dir.name}")
                elif dep_dir.exists() and dep_dir.is_file():
                    dest_path = build_context / dep_dir.name
                    shutil.copy2(dep_dir, dest_path)
                    logger.info(f"Copied local dependency file: {dep_dir.name}")
                else:
                    logger.warning(f"Local dependency not found: {dep_path}")

        # Generate requirements.txt
        self._generate_requirements(agent_path, build_context, framework_config)

        # Generate Dockerfile
        dockerfile_content = self.generate_dockerfile(agent_path, metadata, base_image)
        (build_context / "Dockerfile").write_text(dockerfile_content)

        # Generate framework-specific entrypoint
        entrypoint_content = self.generate_entrypoint(agent_path, metadata, add_ui)
        entrypoint_filename = framework_config["entrypoint_script"]
        (build_context / entrypoint_filename).write_text(entrypoint_content)

        # Copy chat handler files
        self._copy_chat_handler_files(build_context)

        # Copy UI files if enabled
        if add_ui:
            self._copy_spa_files(build_context, metadata, port)

        logger.info(f"Created unified Docker build context at {build_context}")
        return build_context

    def _generate_requirements(
        self, agent_path: Path, build_context: Path, framework_config: Dict
    ) -> None:
        """Generate requirements.txt with framework-specific dependencies.

        Ensures 100% of agent-specific dependencies are preserved while adding
        framework-specific A2A dependencies.
        """
        req_file = agent_path / "requirements.txt"
        requirements_content = ""

        if req_file.exists():
            existing_content = req_file.read_text().strip()
            lines = existing_content.split("\n")

            # Preserve ALL existing requirements (including comments)
            agent_requirements = []
            for line in lines:
                agent_requirements.append(line)

            # Extract existing requirements for comparison (including extras)
            existing_requirements = set()
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Normalize requirement (remove version constraints for comparison)
                    normalized = (
                        line.split(">=")[0]
                        .split("==")[0]
                        .split("!=")[0]
                        .split(">")[0]
                        .split("<")[0]
                        .strip()
                    )
                    existing_requirements.add(normalized.lower())

            # Add framework dependencies that aren't already present
            framework_additions = []
            for dep in framework_config["dependencies"]:
                # Normalize framework dependency for comparison
                normalized_dep = (
                    dep.split(">=")[0]
                    .split("==")[0]
                    .split("!=")[0]
                    .split(">")[0]
                    .split("<")[0]
                    .strip()
                )
                if normalized_dep.lower() not in existing_requirements:
                    framework_additions.append(dep)

            # Combine: agent requirements first, then framework additions
            if framework_additions:
                requirements_content = (
                    "\n".join(agent_requirements)
                    + "\n\n# Framework-specific A2A dependencies\n"
                    + "\n".join(framework_additions)
                )
            else:
                requirements_content = "\n".join(agent_requirements)
        else:
            # Create requirements with framework dependencies
            requirements_content = (
                "# Framework-specific dependencies\n"
                + "\n".join(framework_config["dependencies"])
                + "\n\n# Additional utilities\nrequests\n"
            )

        (build_context / "requirements.txt").write_text(requirements_content)

    def _copy_chat_handler_files(self, build_context: Path) -> None:
        """Copy chat handler files, core modules, and shared modules for runtime import."""
        import shutil

        # Copy API files
        any_agent_api_dir = build_context / "any_agent" / "api"
        any_agent_api_dir.mkdir(parents=True, exist_ok=True)

        api_source_dir = Path(__file__).parent.parent / "api"
        chat_files = ["__init__.py", "chat_handler.py", "unified_a2a_client_helper.py"]

        for py_file in chat_files:
            source_file = api_source_dir / py_file
            if source_file.exists():
                shutil.copy2(source_file, any_agent_api_dir / py_file)
            elif py_file == "__init__.py":
                (any_agent_api_dir / py_file).write_text("")

        # Copy core files (needed for context isolation)
        any_agent_core_dir = build_context / "any_agent" / "core"
        any_agent_core_dir.mkdir(parents=True, exist_ok=True)

        core_source_dir = Path(__file__).parent.parent / "core"
        core_files = ["__init__.py", "context_aware_wrapper.py"]

        for py_file in core_files:
            source_file = core_source_dir / py_file
            if source_file.exists():
                shutil.copy2(source_file, any_agent_core_dir / py_file)
            elif py_file == "__init__.py":
                (any_agent_core_dir / py_file).write_text("")

        # Copy shared files (needed for unified generators)
        any_agent_shared_dir = build_context / "any_agent" / "shared"
        any_agent_shared_dir.mkdir(parents=True, exist_ok=True)

        shared_source_dir = Path(__file__).parent.parent / "shared"
        shared_files = [
            "__init__.py",
            "strands_context_executor.py",
            "entrypoint_templates.py",
            "chat_endpoints_generator.py",
            "ui_routes_generator.py",
            "url_builder.py",
            "url_utils.py",
        ]

        for py_file in shared_files:
            source_file = shared_source_dir / py_file
            if source_file.exists():
                shutil.copy2(source_file, any_agent_shared_dir / py_file)
                logger.info(f"Copied shared file: {py_file}")
            elif py_file == "__init__.py":
                (any_agent_shared_dir / py_file).write_text("")

        # Create any_agent/__init__.py to make it importable
        any_agent_init = build_context / "any_agent" / "__init__.py"
        if not any_agent_init.exists():
            any_agent_init.write_text("")

    def _copy_spa_files(
        self, build_context: Path, metadata: AgentMetadata, port: int
    ) -> None:
        """Copy React SPA files from the built UI to build context."""
        from ..ui.manager import UIBuildManager

        ui_manager = UIBuildManager()
        copy_result = ui_manager.copy_dist_to_context(build_context)

        if not copy_result["success"]:
            logger.warning(f"Failed to copy UI files: {copy_result['error']}")
            self._create_fallback_index_html(build_context, metadata, port)
        else:
            logger.info(
                f"Copied {copy_result['files_copied']} UI files to build context"
            )

    def _create_fallback_index_html(
        self, build_context: Path, metadata: AgentMetadata, port: int
    ) -> None:
        """Create fallback HTML when React SPA is not available."""
        static_dir = build_context / "static"
        static_dir.mkdir(parents=True, exist_ok=True)

        fallback_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{metadata.name} - Any Agent</title>
    <style>
        body {{ font-family: system-ui, sans-serif; margin: 0; padding: 2rem; background: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .header {{ color: #1f4788; margin-bottom: 2rem; }}
        .framework-badge {{ background: #e3f2fd; color: #1565c0; padding: 0.25rem 0.75rem; border-radius: 1rem; font-size: 0.8rem; }}
        .info {{ background: #f8f9fa; padding: 1.5rem; border-radius: 4px; margin: 1rem 0; }}
        .status {{ color: #006b3c; font-weight: bold; }}
        .endpoints {{ margin: 2rem 0; }}
        .endpoint {{ background: #fff; border: 1px solid #dee2e6; padding: 1rem; margin: 0.5rem 0; border-radius: 4px; }}
        .method {{ background: #1f4788; color: white; padding: 0.25rem 0.5rem; border-radius: 3px; font-size: 0.8rem; }}
        code {{ background: #f1f3f4; padding: 0.25rem 0.5rem; border-radius: 3px; font-family: monospace; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Any Agent</h1>
            <h2>{metadata.name} <span class="framework-badge">{metadata.framework.replace("_", " ").title()}</span></h2>
        </div>
        
        <div class="info">
            <h3>Agent Information</h3>
            <p><strong>Framework:</strong> {metadata.framework.replace("_", " ").title()}</p>
            <p><strong>Model:</strong> {metadata.model}</p>
            <p><strong>Port:</strong> {port}</p>
            <p><strong>Status:</strong> <span class="status">Active</span></p>
        </div>
        
        <div class="endpoints">
            <h3>Available Endpoints</h3>
            <div class="endpoint">
                <span class="method">GET</span> <code><a href="/health">/health</a></code> - Health check
            </div>
            <div class="endpoint">
                <span class="method">GET</span> <code><a href="/.well-known/agent-card.json">/.well-known/agent-card.json</a></code> - Agent discovery
            </div>
            <div class="endpoint">
                <span class="method">POST</span> <code>/message:send</code> - Send message to agent
            </div>
        </div>
        
        <footer style="text-align: center; margin-top: 2rem; color: #6c757d; font-size: 0.9rem;">
            <p>{metadata.framework.replace("_", " ").title()} Agent • Powered by Any Agent Framework</p>
        </footer>
    </div>
</body>
</html>"""

        (static_dir / "index.html").write_text(fallback_html)
        logger.info(f"Created fallback HTML interface at {static_dir / 'index.html'}")

    def generate_docker_commands(
        self, build_context: Path, metadata: AgentMetadata
    ) -> List[str]:
        """Generate Docker build and run commands."""
        framework_config = self.get_framework_config(metadata.framework)
        port = framework_config["default_port"]
        image_name = (
            f"{metadata.name.lower().replace('_', '-').replace(' ', '-')}-agent"
        )

        commands = [
            "# Build Docker image",
            f"cd {build_context}",
            f"docker build -t {image_name}:latest .",
            "",
            "# Run container",
            f"docker run -d --restart=always --name {image_name}-container -p {port}:{port} {image_name}:latest",
            "",
            "# Check health",
            "sleep 15  # Wait for startup",
            f"curl {localhost_urls.health_url(port)}",
            "",
            "# Test endpoints",
            f"curl {localhost_urls.agent_card_url(port)}",
        ]

        return commands

    def _generate_chat_endpoints(self, framework_type: str) -> str:
        """Generate chat endpoints code - delegated to ChatEndpointsGenerator."""
        request_style = (
            "starlette" if framework_type in ["adk", "strands"] else "fastapi"
        )
        return self.chat_endpoints_generator.generate_chat_endpoints(
            framework_type, request_style, "localhost"
        )

    def _generate_adk_entrypoint(
        self, agent_path: Path, metadata: AgentMetadata, add_ui: bool = False
    ) -> str:
        """Generate ADK entrypoint - legacy method for compatibility."""
        return self.generate_entrypoint(agent_path, metadata, add_ui)

    def _generate_strands_entrypoint(
        self, agent_path: Path, metadata: AgentMetadata, add_ui: bool = False
    ) -> str:
        """Generate Strands entrypoint - legacy method for compatibility."""
        return self.generate_entrypoint(agent_path, metadata, add_ui)
