"""
Simple Sally - LangGraph Agent

A minimal LangGraph agent demonstrating stateful agent patterns with tools.
Uses modern LangGraph patterns for 2025.
"""

import os
from pathlib import Path
from typing import Any, Dict

# Load environment variables
try:
    from dotenv import load_dotenv

    # Search current directory and up to 3 parent folders for .env
    current_path = Path(__file__).parent
    env_path = current_path / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        for i in range(min(3, len(Path(__file__).parents))):
            env_path = Path(__file__).parents[i] / ".env"
            if env_path.exists():
                load_dotenv(env_path)
                break
except ImportError:
    pass

# Core LangGraph imports
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

# Simple tools using LangGraph @tool decorator
@tool
def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"The weather in {city} is sunny and 72°F."

@tool
def calculate(expression: str) -> str:
    """Safely evaluate mathematical expressions."""
    try:
        # Only allow basic math operations for safety
        allowed_chars = "0123456789+-*/.() "
        if all(c in allowed_chars for c in expression):
            result = eval(expression)
            return f"The result of {expression} is {result}"
        else:
            return "Error: Only basic math operations are allowed."
    except Exception as e:
        return f"Error calculating {expression}: {str(e)}"

@tool
def get_time() -> str:
    """Get the current time."""
    from datetime import datetime
    return f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

@tool
def remember_info(info: str) -> str:
    """Remember information for later use in the conversation."""
    return f"I'll remember: {info}"

# Tools list
tools = [get_weather, calculate, get_time, remember_info]

def create_agent():
    """Create Simple Sally agent with LangGraph."""

    # Initialize the language model
    llm = ChatOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4.1-mini",
        temperature=0.3
    )

    # Create memory saver for state persistence
    memory = MemorySaver()

    # Create the LangGraph agent
    agent = create_react_agent(
        model=llm,
        tools=tools,
        checkpointer=memory
    )

    return agent

# Module-level agent
root_agent = create_agent()

def run_agent(query: str, thread_id: str = "default") -> Dict[str, Any]:
    """Run the agent with a query and thread ID for conversation continuity."""
    try:
        config = {"configurable": {"thread_id": thread_id}}
        messages = [{"role": "user", "content": query}]

        # Stream the response
        result = None
        for chunk in root_agent.stream({"messages": messages}, config):
            result = chunk

        return result
    except Exception as e:
        return {"error": str(e), "query": query}

if __name__ == "__main__":
    agent = create_agent()
    print("✓ Simple Sally (LangGraph) ready!")
    print("✓ Tools: Weather, Calculator, Time, Memory")
    print("✓ Model: GPT-4.1-mini")
    print("✓ Features: Stateful conversations with memory")

    # Test interaction
    try:
        test_query = "What's the weather in Boston and remember that I live there."
        print(f"\nTest Query: {test_query}")

        config = {"configurable": {"thread_id": "test"}}
        response = agent.invoke(
            {"messages": [{"role": "user", "content": test_query}]},
            config
        )

        # Extract the final message
        if "messages" in response and response["messages"]:
            final_message = response["messages"][-1]
            if hasattr(final_message, 'content'):
                print(f"Response: {final_message.content}")
            else:
                print(f"Response: {final_message}")
        else:
            print(f"Response: {response}")

    except Exception as e:
        print(f"Error: {e}")