"""Consolidated URL builder for Any Agent framework.

Centralizes all URL construction patterns to eliminate duplication across:
- chat_endpoints_generator.py
- entrypoint_templates.py
- api/chat_handler.py
- Docker/localhost specific patterns
"""

import os
from typing import Optional
from .url_utils import localhost_urls, AgentURLBuilder


class ConsolidatedURLBuilder:
    """Consolidated URL builder that handles all framework URL patterns."""

    def __init__(self, deployment_type: str = "docker"):
        """Initialize builder for specific deployment type.

        Args:
            deployment_type: Either "docker" or "localhost"
        """
        self.deployment_type = deployment_type
        self.localhost_builder = localhost_urls

    def default_agent_url(self, port: Optional[int] = None) -> str:
        """Build default agent URL based on deployment type.

        Args:
            port: Optional port override

        Returns:
            Default agent URL for current deployment context
        """
        if self.deployment_type == "localhost":
            port = port or int(os.getenv("AGENT_PORT", "8080"))
            return self.localhost_builder.base_url(port)
        else:
            # Docker deployment - use environment port
            port = port or int(os.getenv("AGENT_PORT", "8080"))
            return f"http://localhost:{port}"

    def agent_url_with_fallback(self, provided_url: Optional[str], port: Optional[int] = None) -> str:
        """Get agent URL with fallback to default.

        Args:
            provided_url: User-provided URL (may be None)
            port: Optional port for fallback URL

        Returns:
            Provided URL or default if None
        """
        return provided_url or self.default_agent_url(port)

    def build_chat_endpoint_urls(self, port: int) -> dict[str, str]:
        """Build all URLs needed for chat endpoints.

        Args:
            port: Agent port

        Returns:
            Dictionary with chat-related URLs
        """
        base = self.default_agent_url(port)
        return {
            "agent_base": base,
            "health": f"{base}/health",
            "agent_card": f"{base}/.well-known/agent-card.json"
        }

    def get_environment_port(self, default: int = 8080) -> int:
        """Get port from AGENT_PORT environment variable.

        Args:
            default: Default port if env var not set

        Returns:
            Port number from environment or default
        """
        try:
            return int(os.getenv("AGENT_PORT", str(default)))
        except (ValueError, TypeError):
            return default


# Singleton instances for common use cases
docker_url_builder = ConsolidatedURLBuilder("docker")
localhost_url_builder = ConsolidatedURLBuilder("localhost")


def get_url_builder(deployment_type: str) -> ConsolidatedURLBuilder:
    """Get URL builder for specific deployment type.

    Args:
        deployment_type: Either "docker" or "localhost"

    Returns:
        ConsolidatedURLBuilder instance
    """
    if deployment_type == "localhost":
        return localhost_url_builder
    else:
        return docker_url_builder