"""Shared UI routes generator for serving React SPA."""

import logging
from .unified_ui_routes import unified_ui_generator, UIConfig

logger = logging.getLogger(__name__)


class UIRoutesGenerator:
    """Generate UI serving routes for both localhost and docker pipelines.

    Now uses unified UI route generation system to eliminate duplication.
    """

    def generate_ui_routes(
        self, add_ui: bool, framework: str = "generic", request_style: str = "starlette"
    ) -> str:
        """Generate UI serving routes if enabled.

        Args:
            add_ui: Whether to add UI routes
            framework: Framework type ("adk", "strands", "generic")
            request_style: "starlette" or "fastapi" (deprecated - auto-selected)

        Returns:
            Generated UI routes code as string
        """
        config = UIConfig(
            add_ui=add_ui,
            framework=framework,
            deployment_type="docker",  # Default for backward compatibility
        )
        return unified_ui_generator.generate_ui_routes(config)

    # Legacy methods removed - now use unified_ui_generator

    def generate_localhost_ui_routes(
        self, add_ui: bool, port: int, agent_name: str
    ) -> str:
        """Generate localhost-specific UI routes with proper path handling."""
        return unified_ui_generator.generate_localhost_ui_routes(
            add_ui, port, agent_name, framework="generic"
        )
