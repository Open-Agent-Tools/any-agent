"""Agent context tracking for build and removal operations."""

import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


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

    # Docker artifacts
    container_name: Optional[str] = None
    container_id: Optional[str] = None
    image_name: Optional[str] = None
    image_id: Optional[str] = None
    port: Optional[int] = None

    # Helmsman integration
    helmsman_agent_id: Optional[str] = None
    helmsman_url: Optional[str] = None

    # Build artifacts
    build_context_path: Optional[str] = None
    dockerfile_path: Optional[str] = None

    # Status tracking
    status: str = "built"  # built, running, stopped, removed
    removal_log: List[Dict[str, Any]] = field(default_factory=list)

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
        """Update context with container information."""
        context = self.load_context()
        if not context:
            logger.warning("No context found to update container info")
            return

        context.container_name = container_name
        context.container_id = container_id
        context.port = port
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

        if context.container_name:
            artifacts["containers"] = [context.container_name]
        if context.image_name:
            artifacts["images"] = [context.image_name]
        if context.helmsman_agent_id:
            artifacts["helmsman_ids"] = [context.helmsman_agent_id]
        if context.build_context_path:
            artifacts["build_contexts"] = [context.build_context_path]

        return artifacts

    def context_exists(self) -> bool:
        """Check if context file exists."""
        return self.context_file.exists()

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
