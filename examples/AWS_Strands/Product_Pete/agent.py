"""Product Pete: A Product Manager AI assistant built with Strands Agents"""

import logging
import os
from pathlib import Path
from strands import Agent
from strands.models.anthropic import AnthropicModel
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp.mcp_client import MCPClient

# Import prompts
try:
    from .prompts import SYSTEM_PROMPT
except ImportError:
    from prompts import SYSTEM_PROMPT  # type: ignore

# Load environment variables from .env file
from dotenv import load_dotenv

# Load .env file from current directory only
current_dir = Path(__file__).parent
env_file = current_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)
else:
    # Also try loading from default location if current dir doesn't have it
    load_dotenv()

# Setup simplified logging (warn/debug/error only)
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def add_mcp_tools(base_tools: list, mcp_url: str):
    """Add MCP tools to base tools list - handle failures gracefully for containerization."""
    logger.info(f"Connecting to MCP server at {mcp_url}")
    
    try:
        mcp_client = MCPClient(lambda: streamablehttp_client(mcp_url))
        mcp_client.start()
        mcp_tools = list(mcp_client.list_tools_sync())
        base_tools.extend(mcp_tools)
        
        logger.info(f"Successfully added {len(mcp_tools)} MCP tools")
        return base_tools
    except Exception as e:
        logger.warning(f"Failed to connect to MCP server at {mcp_url}: {e}")
        logger.warning("Agent will start without MCP tools - they may be available later")
        return base_tools


def create_agent():
    """Create Product Pete agent with MCP tools."""
    tools =[]
    # Add MCP tools - handle failures gracefully
    mcp_url = os.getenv("MCP_SERVER_URL", "http://localhost:9000/mcp/")
    tools = add_mcp_tools(tools, mcp_url)
    
    # Create the Anthropic model with Claude Sonnet 4
    model = AnthropicModel(
        client_args={
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
        },
        model_id="claude-sonnet-4-20250514",
        max_tokens=32768,
        params={
            "temperature": 0.7,
        }
    )
    
    # Create the agent
    return Agent(
        model=model,
        name="Product Pete",
        description="A Product Manager AI assistant built with Strands Agents",
        tools=tools,
        system_prompt=SYSTEM_PROMPT
    )

# Create the root agent
root_agent = create_agent()

# Simple test function for local execution
def main():
    """Simple test function to verify Product Pete works."""
    print("Testing Product Pete...")
    
    try:
        response = root_agent("Hello! Please list the names of available jira projects.")
        print(f"Agent Response: {response}")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()