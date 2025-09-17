"""Agent context tracking for build and removal operations."""

import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class LocalhostServerInfo:
    """Information about a localhost development server."""

    pid: int
    port: int
    host: str = "localhost"
    app_file_path: Optional[str] = None
    working_directory: Optional[str] = None
    command_line: Optional[str] = None
    start_timestamp: str = ""

    def __post_init__(self):
        if not self.start_timestamp:
            self.start_timestamp = datetime.utcnow().isoformat()


@dataclass
class DockerInstanceInfo:
    """Information about a Docker instance."""

    container_name: str
    container_id: str
    image_name: str
    image_id: str
    port: int
    start_timestamp: str = ""

    def __post_init__(self):
        if not self.start_timestamp:
            self.start_timestamp = datetime.utcnow().isoformat()


@dataclass
class AgentBuildContext:
    """Context information for a built agent."""

    agent_name: str  # Detected agent name from metadata
    framework: str
    model: Optional[str] = None
    version: str = "1.0.0"
    build_timestamp: str = ""
    removal_timestamp: Optional[str] = None

    # Custom names and identifiers
    custom_agent_name: Optional[str] = None  # CLI --agent-name override

    # Deployment mode (can be "mixed" for multiple types)
    deployment_type: str = "docker"  # "docker", "localhost", or "mixed"

    # Multiple Docker instances (supports multiple containers/ports)
    docker_instances: List[DockerInstanceInfo] = field(default_factory=list)

    # Multiple Localhost servers (supports multiple ports)
    localhost_servers: List[LocalhostServerInfo] = field(default_factory=list)

    # Legacy single instance fields (for backward compatibility)
    docker_instance: Optional[DockerInstanceInfo] = None
    localhost_server: Optional[LocalhostServerInfo] = None

    # Helmsman integration
    helmsman_agent_id: Optional[str] = None
    helmsman_url: Optional[str] = None

    # Build artifacts
    build_context_path: Optional[str] = None
    dockerfile_path: Optional[str] = None

    # Status tracking
    status: str = "built"  # built, running, stopped, removed
    removal_log: List[Dict[str, Any]] = field(default_factory=list)

    # Legacy fields for backward compatibility
    container_name: Optional[str] = None
    container_id: Optional[str] = None
    image_name: Optional[str] = None
    image_id: Optional[str] = None
    port: Optional[int] = None

    def __post_init__(self):
        if not self.build_timestamp:
            self.build_timestamp = datetime.utcnow().isoformat()

    def get_effective_agent_name(self) -> str:
        """Get the effective agent name (custom name if provided, otherwise detected name)."""
        return self.custom_agent_name or self.agent_name


class AgentContextManager:
    """Manages .any_agent/context.yaml file for tracking agent state."""

    CONTEXT_DIR = ".any_agent"
    CONTEXT_FILE = "context.yaml"

    def __init__(self, agent_path: Path):
        """Initialize context manager for an agent directory."""
        self.agent_path = Path(agent_path)
        self.context_dir = self.agent_path / self.CONTEXT_DIR
        self.context_file = self.context_dir / self.CONTEXT_FILE

    def ensure_context_dir(self):
        """Ensure .any_agent directory exists."""
        self.context_dir.mkdir(exist_ok=True)

        # Create .gitignore to exclude context from git
        gitignore = self.context_dir / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text("# Any Agent context files\n*.yaml\n*.yml\n*.log\n")

    def load_context(self) -> Optional[AgentBuildContext]:
        """Load existing agent context from file."""
        if not self.context_file.exists():
            return None

        try:
            with open(self.context_file, "r") as f:
                data = yaml.safe_load(f)
                if not data:
                    return None

            # Convert nested dicts to dataclasses
            if "localhost_server" in data and data["localhost_server"]:
                data["localhost_server"] = LocalhostServerInfo(**data["localhost_server"])

            if "docker_instance" in data and data["docker_instance"]:
                data["docker_instance"] = DockerInstanceInfo(**data["docker_instance"])

            # Convert multi-instance lists
            if "localhost_servers" in data and data["localhost_servers"]:
                data["localhost_servers"] = [
                    LocalhostServerInfo(**server_data) for server_data in data["localhost_servers"]
                ]

            if "docker_instances" in data and data["docker_instances"]:
                data["docker_instances"] = [
                    DockerInstanceInfo(**instance_data) for instance_data in data["docker_instances"]
                ]

            # Convert dict back to dataclass
            return AgentBuildContext(**data)

        except Exception as e:
            logger.warning(f"Failed to load context from {self.context_file}: {e}")
            return None

    def save_context(self, context: AgentBuildContext):
        """Save agent context to file."""
        try:
            self.ensure_context_dir()

            with open(self.context_file, "w") as f:
                yaml.safe_dump(asdict(context), f, default_flow_style=False, indent=2)

            logger.debug(f"Saved agent context to {self.context_file}")

        except Exception as e:
            logger.error(f"Failed to save context to {self.context_file}: {e}")
            raise

    def update_build_info(self, **kwargs):
        """Update context with build information."""
        context = self.load_context()
        if not context:
            # Create new context if none exists
            context = AgentBuildContext(
                agent_name=kwargs.get("agent_name", "unknown"),
                framework=kwargs.get("framework", "unknown"),
            )

        # Update with provided information
        for key, value in kwargs.items():
            if hasattr(context, key):
                setattr(context, key, value)

        context.status = "built"
        self.save_context(context)
        return context

    def update_container_info(self, container_name: str, container_id: str, port: int):
        """Update context with container information (legacy method for backward compatibility)."""
        context = self.load_context()
        if not context:
            logger.warning("No context found to update container info")
            return

        # Update both new and legacy fields
        context.container_name = container_name
        context.container_id = container_id
        context.port = port
        context.status = "running"

        self.save_context(context)
        return context

    def update_docker_instance(
        self,
        container_name: str,
        container_id: str,
        image_name: str,
        image_id: str,
        port: int
    ):
        """Update context with Docker instance information."""
        context = self.load_context()
        if not context:
            logger.warning("No context found to update Docker instance info")
            return

        new_instance = DockerInstanceInfo(
            container_name=container_name,
            container_id=container_id,
            image_name=image_name,
            image_id=image_id,
            port=port
        )

        # Add to multi-instance list (remove any existing entry for same container)
        context.docker_instances = [d for d in context.docker_instances if d.container_id != container_id]
        context.docker_instances.append(new_instance)

        # Update legacy fields for backward compatibility
        context.docker_instance = new_instance
        context.container_name = container_name
        context.container_id = container_id
        context.image_name = image_name
        context.image_id = image_id
        context.port = port

        # Update deployment type
        has_docker = bool(context.docker_instances)
        has_localhost = bool(context.localhost_servers or context.localhost_server)
        if has_docker and has_localhost:
            context.deployment_type = "mixed"
        elif has_docker:
            context.deployment_type = "docker"
        else:
            context.deployment_type = "localhost"

        context.status = "running"
        self.save_context(context)
        return context

    def update_localhost_server(
        self,
        pid: int,
        port: int,
        host: str = "localhost",
        app_file_path: Optional[str] = None,
        working_directory: Optional[str] = None,
        command_line: Optional[str] = None
    ):
        """Update context with localhost server information."""
        context = self.load_context()
        if not context:
            logger.warning("No context found to update localhost server info")
            return

        new_server = LocalhostServerInfo(
            pid=pid,
            port=port,
            host=host,
            app_file_path=app_file_path,
            working_directory=working_directory,
            command_line=command_line
        )

        # Add to multi-instance list (remove any existing entry for same port)
        context.localhost_servers = [s for s in context.localhost_servers if s.port != port]
        context.localhost_servers.append(new_server)

        # Update legacy fields for backward compatibility
        context.localhost_server = new_server
        context.port = port

        # Update deployment type
        has_docker = bool(context.docker_instances or context.docker_instance)
        has_localhost = bool(context.localhost_servers)
        if has_docker and has_localhost:
            context.deployment_type = "mixed"
        elif has_localhost:
            context.deployment_type = "localhost"
        else:
            context.deployment_type = "docker"

        context.status = "running"
        self.save_context(context)
        return context

    def update_helmsman_info(self, agent_id: str, helmsman_url: str):
        """Update context with Helmsman registration information."""
        context = self.load_context()
        if not context:
            logger.warning("No context found to update Helmsman info")
            return

        context.helmsman_agent_id = agent_id
        context.helmsman_url = helmsman_url

        self.save_context(context)
        return context

    def mark_removed(self, removal_log: List[Dict[str, Any]]):
        """Mark agent as removed and log the removal details."""
        context = self.load_context()
        if not context:
            logger.warning("No context found to mark as removed")
            return

        context.status = "removed"
        context.removal_timestamp = datetime.utcnow().isoformat()
        context.removal_log = removal_log

        self.save_context(context)
        return context

    def get_removable_artifacts(self) -> Dict[str, Any]:
        """Get list of artifacts that can be removed based on context."""
        context = self.load_context()
        if not context or context.status == "removed":
            return {}

        artifacts = {}

        # Docker artifacts
        if context.docker_instance:
            artifacts["docker_containers"] = [context.docker_instance.container_id]
            artifacts["docker_images"] = [context.docker_instance.image_id]
        elif context.container_name:  # Fallback to legacy fields
            artifacts["docker_containers"] = [context.container_id or context.container_name]
            if context.image_name:
                artifacts["docker_images"] = [context.image_id or context.image_name]

        # Localhost server artifacts
        if context.localhost_server:
            artifacts["localhost_servers"] = [context.localhost_server.pid]

        # Helmsman artifacts
        if context.helmsman_agent_id:
            artifacts["helmsman_ids"] = [context.helmsman_agent_id]

        # Build artifacts
        if context.build_context_path:
            artifacts["build_contexts"] = [context.build_context_path]

        return artifacts

    def get_agent_name(self) -> Optional[str]:
        """Get effective agent name from context (custom name if provided, otherwise detected name)."""
        context = self.load_context()
        return context.get_effective_agent_name() if context else None

    def is_agent_active(self) -> bool:
        """Check if agent is currently active (built/running)."""
        context = self.load_context()
        return bool(context and context.status in ["built", "running"])

    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of current agent status."""
        context = self.load_context()
        if not context:
            return {"status": "not_built", "context_exists": False}

        return {
            "status": context.status,
            "context_exists": True,
            "agent_name": context.agent_name,
            "build_timestamp": context.build_timestamp,
            "removal_timestamp": context.removal_timestamp,
            "has_container": bool(context.container_name),
            "has_image": bool(context.image_name),
            "has_helmsman": bool(context.helmsman_agent_id),
            "port": context.port,
        }
