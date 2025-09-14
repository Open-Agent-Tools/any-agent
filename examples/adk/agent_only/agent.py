"""Generic MCP Test Agent Configuration.

This module configures a standalone test agent for verifying MCP server
connectivity and functionality. It can connect to any MCP server that 
implements the Model Context Protocol.
"""

import logging
import os
import warnings

from google.adk.agents import Agent

from .prompts import agent_instruction
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StreamableHTTPConnectionParams,
)
from dotenv import load_dotenv

try:
    from basic_open_agent_tools import load_all_datetime_tools
except ImportError:
    print("Warning: basic_open_agent_tools not available, datetime tools will not be loaded")
    load_all_datetime_tools = lambda: []

# Initialize environment and logging
load_dotenv()
logging.basicConfig(level=logging.ERROR)
warnings.filterwarnings("ignore")

# Configuration from environment variables only
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:7081/mcp")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-1.5-flash")


def create_agent() -> Agent:
    """
    Creates and returns a configured generic test agent instance.

    Returns:
        Agent: Configured test agent with MCP connectivity.
    """

    # Load datetime tools for natural language time handling
    date_tools = load_all_datetime_tools()

    # Docker URL translation for MCP servers
    def translate_docker_url(url: str) -> str:
        """Translate localhost URLs to Docker-accessible URLs when running in container."""
        if "localhost" in url or "127.0.0.1" in url:
            # Check if we're running in Docker (common indicators)
            if os.path.exists("/.dockerenv") or os.getenv("DOCKER_CONTAINER"):
                # Replace localhost with host.docker.internal for Docker Desktop
                # or with the actual host IP for Linux Docker
                if "localhost:7081" in url:
                    return url.replace("localhost:7081", "host.docker.internal:7081")
                elif "127.0.0.1:7081" in url:
                    return url.replace("127.0.0.1:7081", "host.docker.internal:7081")
        return url

    # Translate MCP server URL for Docker environment
    docker_mcp_url = translate_docker_url(MCP_SERVER_URL)
    
    # Try to include MCP tools with Docker URL translation
    agent_tools = date_tools
    try:
        mcp_toolset = [
            MCPToolset(
                connection_params=StreamableHTTPConnectionParams(
                    url=docker_mcp_url,
                ),
            ),
        ]
        agent_tools = mcp_toolset + date_tools
        print(f"Successfully configured MCP tools for {docker_mcp_url} (translated from {MCP_SERVER_URL})")
    except Exception as e:
        print(f"Warning: Could not configure MCP tools for {docker_mcp_url}: {e}, using basic tools only")

    return Agent(
        model=GOOGLE_MODEL,
        name="Testing_Tessie",
        instruction=agent_instruction,
        description="Generic test agent for validating MCP server connectivity and tool operations with datetime support.",
        tools=agent_tools,
    )


# Configure generic test agent
root_agent = create_agent()