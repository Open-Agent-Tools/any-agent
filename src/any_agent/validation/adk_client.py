"""ADK-based A2A Testing Client using RemoteA2aAgent."""

from typing import Optional
from dataclasses import dataclass

try:
    from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH
    from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
    from google.adk import Agent

    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    AGENT_CARD_WELL_KNOWN_PATH = ".well-known/agent.json"
    RemoteA2aAgent = None
    Agent = None


@dataclass
class ADKTestResult:
    """Result from ADK-based A2A agent interaction."""

    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    agent_name: Optional[str] = None
    execution_time_ms: Optional[float] = None


class ADKTestClient:
    """Test client using Google ADK RemoteA2aAgent for A2A communication."""

    def __init__(self, agent_url: str, agent_name: str = "test_agent"):
        """Initialize ADK test client.

        Args:
            agent_url: Base URL of the A2A agent (e.g., "http://localhost:8035")
            agent_name: Name for the RemoteA2aAgent wrapper
        """
        if not ADK_AVAILABLE:
            raise ImportError(
                "Google ADK is not available. Install google-adk to use ADK-based testing."
            )

        self.agent_url = agent_url.rstrip("/")
        self.agent_name = agent_name
        self.remote_agent: Optional[RemoteA2aAgent] = None

    def create_test_agent(
        self, description: str = "Test agent for A2A validation"
    ) -> Agent:
        """Create test agent with RemoteA2aAgent as sub-agent."""
        if not ADK_AVAILABLE:
            raise ImportError("Google ADK is not available.")

        agent_card_url = f"{self.agent_url}/{AGENT_CARD_WELL_KNOWN_PATH}"

        # Create RemoteA2aAgent as sub-agent
        remote_agent = RemoteA2aAgent(
            name=f"{self.agent_name}_remote",
            description=f"Remote connection to agent at {self.agent_url}",
            agent_card=agent_card_url,
        )

        # Create main test agent that uses the remote agent as a tool
        test_agent = Agent(
            model="gemini-2.0-flash",  # Required for ADK Agent
            name=self.agent_name,
            instruction="""
            You are a test agent that communicates with a remote A2A agent for validation purposes.
            Use the remote agent tool to interact with the remote agent and provide responses back to the user.
            """,
            tools=[remote_agent],  # Include remote agent as a tool
        )

        self.test_agent = test_agent
        self.remote_agent = remote_agent

        return test_agent

    async def test_conversation(self, message: str) -> ADKTestResult:
        """Test conversational interaction with the A2A agent.

        Args:
            message: Message to send to the agent

        Returns:
            ADKTestResult with response or error information
        """
        if not hasattr(self, "test_agent"):
            self.create_test_agent()

        import time

        start_time = time.time()

        try:
            # Use ADK Runner to execute the agent with the message
            from google.adk import Runner

            runner = Runner(self.test_agent)
            response = await runner.run(message)

            execution_time_ms = (time.time() - start_time) * 1000

            # Extract the response text
            response_text = str(response) if response else "No response"

            return ADKTestResult(
                success=True,
                response=response_text,
                agent_name=self.agent_name,
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return ADKTestResult(
                success=False,
                error=str(e),
                agent_name=self.agent_name,
                execution_time_ms=execution_time_ms,
            )

    def get_agent_card_url(self) -> str:
        """Get the agent card URL for this agent."""
        return f"{self.agent_url}/{AGENT_CARD_WELL_KNOWN_PATH}"

    async def validate_agent_card_accessibility(self) -> ADKTestResult:
        """Test if the agent card is accessible."""
        import httpx
        import time

        start_time = time.time()
        agent_card_url = self.get_agent_card_url()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(agent_card_url)
                execution_time_ms = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    return ADKTestResult(
                        success=True,
                        response=f"Agent card accessible: {len(response.text)} bytes",
                        execution_time_ms=execution_time_ms,
                    )
                else:
                    return ADKTestResult(
                        success=False,
                        error=f"Agent card returned status {response.status_code}",
                        execution_time_ms=execution_time_ms,
                    )
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return ADKTestResult(
                success=False,
                error=f"Failed to access agent card: {e}",
                execution_time_ms=execution_time_ms,
            )


def is_adk_available() -> bool:
    """Check if Google ADK is available for use."""
    return ADK_AVAILABLE


# Convenience function for quick testing
async def test_a2a_agent(
    agent_url: str, message: str = "Hello! What is your name?"
) -> ADKTestResult:
    """Quick test function for A2A agent communication.

    Args:
        agent_url: URL of the A2A agent to test
        message: Message to send to the agent

    Returns:
        ADKTestResult with the interaction result
    """
    if not ADK_AVAILABLE:
        return ADKTestResult(
            success=False,
            error="Google ADK is not available. Install google-adk package.",
        )

    client = ADKTestClient(agent_url)
    return await client.test_conversation(message)
