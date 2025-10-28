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
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8080/mcp")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")


def create_agent() -> Agent:
    """
    Creates and returns a configured generic test agent instance.

    Returns:
        Agent: Configured test agent with MCP connectivity.
    """

    # Load datetime tools for natural language time handling
    date_tools = load_all_datetime_tools()

    # Try to include MCP tools if MCP_SERVER_URL is configured
    agent_tools = date_tools
    if MCP_SERVER_URL:
        try:
            mcp_toolset = [
                MCPToolset(
                    connection_params=StreamableHTTPConnectionParams(
                        url=MCP_SERVER_URL,
                    ),
                ),
            ]
            agent_tools = date_tools + mcp_toolset
            print(f"Successfully configured MCP tools for {MCP_SERVER_URL}")
        except Exception as e:
            print(
                f"Warning: Could not configure MCP tools for {MCP_SERVER_URL}: {e}, using basic tools only"
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
