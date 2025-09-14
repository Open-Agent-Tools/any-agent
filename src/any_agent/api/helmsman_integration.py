"""Helmsman integration for agent registration and discovery."""

import logging
import requests
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

from ..adapters.base import AgentMetadata

logger = logging.getLogger(__name__)


@dataclass
class AgentEndpoints:
    """Standard endpoints exposed by the agent."""

    health: str = "/health"
    chat: str = "/"
    describe: str = "/describe"


@dataclass
class HelsmanAgentMetadata:
    """Metadata structure for Helmsman agent registration."""

    version: str
    environment: str
    capabilities: List[str]


@dataclass
class HelsmanRegistration:
    """Complete agent registration data for Helmsman."""

    name: str
    description: str
    agent_type: str
    root_url: str
    docker_endpoint: str
    endpoints: AgentEndpoints
    metadata: HelsmanAgentMetadata


class HelsmanClient:
    """Client for interacting with Helmsman API."""

    def __init__(self, base_url: str = "http://localhost:7080", timeout: int = 30):
        """
        Initialize Helmsman client.

        Args:
            base_url: Base URL of Helmsman service
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def register_agent(self, registration: HelsmanRegistration) -> Dict[str, Any]:
        """
        Register an agent with Helmsman.

        Args:
            registration: Agent registration data

        Returns:
            Registration response from Helmsman

        Raises:
            requests.RequestException: If registration fails
        """
        url = f"{self.base_url}/api/agents"

        # Convert to dict and handle nested dataclasses
        payload = asdict(registration)

        logger.info(f"Registering agent with Helmsman at {url}")
        logger.info(f"Registration payload: {payload}")

        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Agent successfully registered with Helmsman: {result}")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to register agent with Helmsman: {e}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.error(f"Helmsman error response: {error_detail}")
                except Exception:
                    logger.error(f"Helmsman error response: {e.response.text}")
            raise

    def unregister_agent(self, agent_name: str) -> bool:
        """
        Unregister an agent from Helmsman.

        Args:
            agent_name: Name of agent to unregister

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/api/agents/{agent_name}"

        try:
            response = self.session.delete(url, timeout=self.timeout)
            response.raise_for_status()

            logger.info(f"Agent {agent_name} unregistered from Helmsman")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to unregister agent {agent_name}: {e}")
            return False

    def check_agent_status(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Check agent status in Helmsman.

        Args:
            agent_name: Name of agent to check

        Returns:
            Agent status info or None if not found
        """
        url = f"{self.base_url}/api/agents/{agent_name}"

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.debug(f"Agent {agent_name} not found in Helmsman: {e}")
            return None

    def health_check(self) -> bool:
        """
        Check if Helmsman service is healthy.

        Returns:
            True if Helmsman is responding, False otherwise
        """
        url = f"{self.base_url}/api/health"

        try:
            response = self.session.get(url, timeout=10)  # Increased timeout
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"Helmsman health check: {response.status_code} from {url}")
            return response.status_code == 200

        except requests.exceptions.RequestException as e:
            # Log the actual error for debugging
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Helmsman health check failed at {url}: {e}")
            return False

    def list_agents(self) -> Optional[Dict[str, Any]]:
        """
        List all agents in Helmsman.

        Returns:
            Dictionary with agents list or None if failed
        """
        url = f"{self.base_url}/api/agents"

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list agents from Helmsman: {e}")
            return None

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific agent by ID from Helmsman.

        Args:
            agent_id: Unique agent ID

        Returns:
            Agent info or None if not found
        """
        url = f"{self.base_url}/api/agents/{agent_id}"

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.debug(f"Agent {agent_id} not found in Helmsman: {e}")
            return None

    def delete_agent(self, agent_id: str) -> bool:
        """
        Delete agent by ID from Helmsman.

        Args:
            agent_id: Unique agent ID to delete

        Returns:
            True if successfully deleted, False otherwise
        """
        url = f"{self.base_url}/api/agents/{agent_id}"

        try:
            response = self.session.delete(url, timeout=self.timeout)
            response.raise_for_status()

            logger.info(f"Successfully deleted agent {agent_id} from Helmsman")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to delete agent {agent_id}: {e}")
            return False


def create_helmsman_registration(
    metadata: AgentMetadata,
    root_url: str,
    docker_endpoint: str,
    agent_id: Optional[str] = None,
    environment: str = "development",
    version: str = "1.0.0",
) -> HelsmanRegistration:
    """
    Create a Helmsman registration from agent metadata.

    Args:
        metadata: Agent metadata from detection
        root_url: Root URL where agent is accessible (external)
        docker_endpoint: Docker container endpoint (internal)
        agent_id: Custom agent identifier (defaults to metadata.name)
        environment: Deployment environment
        version: Agent version

    Returns:
        HelsmanRegistration ready for submission
    """

    # Determine agent type from framework - must be 'adk', 'strands', 'crewai' or 'langchain'
    agent_type_mapping = {
        "google_adk": "adk",
        "aws_strands": "strands",
        "langchain": "langchain",
        "crewai": "crewai",
    }

    # Ensure agent type is one of the accepted values
    agent_type = agent_type_mapping.get(
        metadata.framework, "adk"
    )  # Default to 'adk' for unknown frameworks

    # Validate agent type is acceptable
    valid_agent_types = {"adk", "strands", "crewai", "langchain"}
    if agent_type not in valid_agent_types:
        logger.warning(f"Invalid agent type '{agent_type}', defaulting to 'adk'")
        agent_type = "adk"

    # Build capabilities list from framework and tools
    capabilities = []

    # Framework-specific capabilities
    if metadata.framework == "google_adk":
        capabilities.append("adk_framework")
        if metadata.model and "gemini" in metadata.model.lower():
            capabilities.append("gemini_model")

    # Tool-based capabilities
    if metadata.tools:
        for tool in metadata.tools:
            tool_name = tool.lower().replace(" ", "_")
            capabilities.append(f"tool_{tool_name}")

    # Add general capabilities
    capabilities.extend(["natural_language", "context_awareness"])

    return HelsmanRegistration(
        name=agent_id or metadata.name,
        description=metadata.description or f"{metadata.name} agent",
        agent_type=agent_type,
        root_url=root_url,
        docker_endpoint=docker_endpoint,
        endpoints=AgentEndpoints(),
        metadata=HelsmanAgentMetadata(
            version=version, environment=environment, capabilities=capabilities
        ),
    )
