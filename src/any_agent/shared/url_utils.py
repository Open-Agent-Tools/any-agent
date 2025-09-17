"""Centralized URL utilities for Any Agent framework.

Provides consistent URL construction and validation across the codebase,
eliminating duplication of URL handling patterns.
"""



class AgentURLBuilder:
    """Builder for standard agent endpoint URLs."""

    def __init__(self, host: str = "localhost", scheme: str = "http"):
        """Initialize URL builder with host and scheme defaults."""
        self.host = host
        self.scheme = scheme

    def base_url(self, port: int) -> str:
        """Build base URL for an agent."""
        return f"{self.scheme}://{self.host}:{port}"

    def health_url(self, port: int) -> str:
        """Build health check endpoint URL."""
        return f"{self.base_url(port)}/health"

    def describe_url(self, port: int) -> str:
        """Build describe endpoint URL."""
        return f"{self.base_url(port)}/describe"

    def agent_card_url(self, port: int) -> str:
        """Build agent card endpoint URL."""
        return f"{self.base_url(port)}/.well-known/agent-card.json"

    def agent_json_url(self, port: int) -> str:
        """Build agent.json endpoint URL (legacy)."""
        return f"{self.base_url(port)}/.well-known/agent.json"

    def ui_url(self, port: int, path: str = "") -> str:
        """Build UI endpoint URL with optional path."""
        base = self.base_url(port)
        if path and not path.startswith("/"):
            path = f"/{path}"
        return f"{base}{path}"


class DockerURLBuilder(AgentURLBuilder):
    """URL builder for Docker container networking."""

    def __init__(self, container_name: str, scheme: str = "http"):
        """Initialize with container name as host."""
        super().__init__(host=container_name, scheme=scheme)


# Default builders for common use cases
localhost_urls = AgentURLBuilder()
"""Default localhost URL builder."""


def docker_urls(container_name: str) -> DockerURLBuilder:
    """Create Docker URL builder for a specific container."""
    return DockerURLBuilder(container_name)


def build_agent_urls(
    port: int, host: str = "localhost", scheme: str = "http"
) -> dict[str, str]:
    """Build all standard agent URLs for a given port and host.

    Returns:
        Dictionary with standard endpoint URLs:
        - base: Base URL
        - health: Health check endpoint
        - describe: Describe endpoint
        - agent_card: Agent card endpoint
        - agent_json: Legacy agent.json endpoint
    """
    builder = AgentURLBuilder(host, scheme)
    return {
        "base": builder.base_url(port),
        "health": builder.health_url(port),
        "describe": builder.describe_url(port),
        "agent_card": builder.agent_card_url(port),
        "agent_json": builder.agent_json_url(port),
    }


def is_localhost_url(url: str) -> bool:
    """Check if URL is a localhost URL.

    This is a convenience function that delegates to URLTranslator
    for consistency with existing URL translation logic.
    """
    from ..core.url_translator import URLTranslator

    translator = URLTranslator()
    return translator._looks_like_localhost_url(url)


def validate_agent_url(url: str) -> bool:
    """Validate if URL looks like a valid agent URL.

    Basic validation for agent URLs - checks for proper scheme and structure.
    """
    if not url or not isinstance(url, str):
        return False

    # Must start with http:// or https://
    if not (url.startswith("http://") or url.startswith("https://")):
        return False

    # Basic URL structure validation
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        return bool(parsed.hostname and parsed.port)
    except Exception:
        return False
