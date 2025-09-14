"""FastAPI application generator for localhost development."""

import logging
from pathlib import Path
from typing import Optional

from ..adapters.base import AgentMetadata
from ..shared.entrypoint_templates import UnifiedEntrypointGenerator, EntrypointContext

logger = logging.getLogger(__name__)


class LocalhostFastAPIGenerator:
    """Generates FastAPI applications for localhost development mode."""

    def __init__(self):
        """Initialize the FastAPI generator."""
        self.entrypoint_generator = UnifiedEntrypointGenerator()

    def generate_fastapi_app(
        self,
        agent_path: Path,
        metadata: AgentMetadata,
        output_dir: Optional[Path] = None,
        add_ui: bool = False,
        port: int = 8080,
    ) -> Path:
        """
        Generate FastAPI application file for localhost serving.

        Args:
            agent_path: Path to agent directory
            metadata: Agent metadata from framework adapter
            output_dir: Output directory (defaults to agent_path/.any_agent)
            add_ui: Whether to include UI integration
            port: Port for the application

        Returns:
            Path to generated FastAPI application file
        """
        # Use .any_agent directory as default output
        if output_dir is None:
            output_dir = agent_path / ".any_agent"

        # Ensure output directory exists
        output_dir.mkdir(exist_ok=True)

        # Create context for entrypoint generation
        context = EntrypointContext(
            agent_name=metadata.name,
            agent_path=agent_path,
            framework=metadata.framework,
            port=port,
            add_ui=add_ui,
            deployment_type="localhost",
        )

        # Generate entrypoint content using unified generator
        entrypoint_content = self.entrypoint_generator.generate_entrypoint(context)

        # Write FastAPI app file
        app_file = output_dir / "localhost_app.py"
        app_file.write_text(entrypoint_content)

        logger.info(f"Generated FastAPI app: {app_file}")
        return app_file
