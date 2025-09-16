"""Minimal AWS Strands Agent using Anthropic Claude Sonnet 4.

This is a basic Strands agent implementation without A2A protocol support,
designed for framework detection and basic containerization testing.
"""

import os
from pathlib import Path
from strands import Agent
from strands.models.anthropic import AnthropicModel

# Load environment variables from .env file
from dotenv import load_dotenv

# Load .env file from project root
project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(project_root / ".env")

# Create the Anthropic model with Claude Sonnet 4
model = AnthropicModel(
    client_args={
        "api_key": os.getenv("ANTHROPIC_API_KEY"),
    },
    model_id="claude-sonnet-4-20250514",
    max_tokens=1024,
    params={
        "temperature": 0.7,
    },
)

# Create the root agent
root_agent = Agent(
    model=model,
    name="Minimal Strands Agent",
    description="A minimal AWS Strands agent using Anthropic Claude Sonnet 4 for basic conversation",
    system_prompt=(
        "You are the 'Minimal Strands Agent', a helpful AI assistant built using AWS Strands framework. "
        "When introducing yourself, identify as the 'Minimal Strands Agent' rather than Claude. "
        "You can engage in conversations and answer questions to the best of your ability."
    ),
)


# Simple test function for local execution
def main():
    """Simple test function to verify the agent works."""
    print("Testing Minimal Strands Agent...")

    try:
        response = root_agent("Hello! Please introduce yourself.")
        print(f"Agent Response: {response}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
