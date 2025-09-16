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
    print(
        "Warning: basic_open_agent_tools not available, datetime tools will not be loaded"
    )
    load_all_datetime_tools = lambda: []

# Initialize environment and logging
load_dotenv()
logging.basicConfig(level=logging.ERROR)
warnings.filterwarnings("ignore")

# Configuration from environment variables only
HELMSMAN_MCP_URL = os.getenv("HELMSMAN_MCP_URL", "http://localhost:7081/mcp") # helmsman
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


    # Translate MCP server URL for Docker environment
    # Try to include MCP tools with Docker URL translation
    agent_tools = date_tools
    try:
        mcp_toolset = [
            MCPToolset(
                connection_params=StreamableHTTPConnectionParams(
                    url=HELMSMAN_MCP_URL, #helmsman
                ),
            ),
        ]
        agent_tools = date_tools + mcp_toolset
        print(
            f"Successfully configured MCP tools for {HELMSMAN_MCP_URL} (translated from {HELMSMAN_MCP_URL})"
        )
    except Exception as e:
        print(
            f"Warning: Could not configure MCP tools for {HELMSMAN_MCP_URL}: {e}, using basic tools only"
        )
        agent_tools = date_tools

    return Agent(
        model=GOOGLE_MODEL,
        name="Testing_Tessie",
        instruction=agent_instruction,
        description="Generic test agent for validating MCP server connectivity and tool operations with datetime support.",
        tools=agent_tools,
    )


# Configure generic test agent
root_agent = create_agent()
