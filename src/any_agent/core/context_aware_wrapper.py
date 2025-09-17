"""Context-aware agent wrapper for A2A protocol session isolation.

This module provides automatic context isolation for agents that don't natively
support A2A context_id field. It creates separate agent instances or conversation
contexts per context_id to prevent context bleeding across sessions.
"""

import logging
from typing import Any, Dict, Optional

from .context_manager import create_context_wrapper, BaseContextWrapper

logger = logging.getLogger(__name__)


# Legacy wrapper classes removed in favor of consolidated context_manager system


# Legacy handler functions removed - now handled by consolidated context_manager system


def detect_agent_type(agent: Any) -> str:
    """Detect the agent framework type.

    Args:
        agent: The agent instance to analyze

    Returns:
        Agent framework type string
    """
    agent_module = getattr(agent.__class__, "__module__", "")

    if "strands" in agent_module.lower():
        return "strands"
    elif "google" in agent_module.lower() or "adk" in agent_module.lower():
        return "adk"
    elif "langchain" in agent_module.lower():
        return "langchain"
    elif "crewai" in agent_module.lower():
        return "crewai"
    else:
        return "unknown"


def create_context_aware_strands_agent(original_agent: Any) -> BaseContextWrapper:
    """Create a context-aware wrapper for Strands agents.

    Uses consolidated context management system for consistent behavior.

    Args:
        original_agent: The original Strands agent instance

    Returns:
        Context-aware agent wrapper
    """
    return create_context_wrapper(original_agent, "strands")


def create_context_aware_generic_agent(original_agent: Any) -> BaseContextWrapper:
    """Create a context-aware wrapper for generic agents.

    Uses consolidated context management system for consistent behavior.

    Args:
        original_agent: The original agent instance

    Returns:
        Context-aware agent wrapper
    """
    return create_context_wrapper(original_agent, "generic")


def upgrade_agent_for_context_isolation(agent: Any) -> Any:
    """Upgrade an agent to support A2A context isolation.

    This function analyzes the agent type and applies the appropriate
    context-aware wrapper to prevent context bleeding across sessions.

    Args:
        agent: The original agent instance

    Returns:
        Context-aware agent wrapper
    """
    if agent is None:
        return agent

    # Check if agent already supports context isolation
    if hasattr(agent, "_context_aware_wrapper"):
        logger.info("Agent already has context isolation support")
        return agent

    agent_type = detect_agent_type(agent)
    logger.info(f"🔍 Detected agent type: {agent_type}")

    # Skip context isolation for frameworks that have native support
    if agent_type == "adk":
        logger.info(
            "🔄 Skipping context wrapper for ADK agent (has native A2A context isolation)"
        )
        return agent
    elif agent_type == "strands":
        upgraded_agent = create_context_aware_strands_agent(agent)
    else:
        # Generic approach for other frameworks
        upgraded_agent = create_context_aware_generic_agent(agent)

    # Mark as upgraded
    setattr(upgraded_agent, '_context_aware_wrapper', True)

    logger.info("✅ Agent upgraded for A2A context isolation")
    return upgraded_agent


def extract_structured_message_data_from_a2a(
    message_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Extract structured message data from A2A message including role, parts, messageId, taskId, contextId.

    Args:
        message_data: A2A message dictionary

    Returns:
        Dictionary containing structured message data
    """
    structured_data = {}

    try:
        # Extract text content from message parts
        if "message" in message_data and isinstance(message_data["message"], dict):
            message = message_data["message"]

            # Extract text from parts structure
            if "parts" in message and isinstance(message["parts"], list):
                for part in message["parts"]:
                    if (
                        isinstance(part, dict)
                        and part.get("kind") == "text"
                        and "text" in part
                    ):
                        structured_data["text"] = part["text"]
                        break

            # Extract metadata fields
            structured_data["messageId"] = message.get("messageId")
            structured_data["taskId"] = message.get("taskId")
            structured_data["contextId"] = message.get("contextId")
            structured_data["role"] = message.get("role", "user")

        # Check JSON-RPC nested structure
        elif "params" in message_data and isinstance(message_data["params"], dict):
            params = message_data["params"]
            if "message" in params:
                return extract_structured_message_data_from_a2a(
                    {"message": params["message"]}
                )

        # Fallback: check for direct text content
        if not structured_data.get("text"):
            # Check various common text field locations
            text_locations = ["text", "content", "query", "input"]
            for location in text_locations:
                if location in message_data and message_data[location]:
                    structured_data["text"] = str(message_data[location])
                    break

        # Extract context_id from various locations if not found
        if not structured_data.get("contextId"):
            structured_data["contextId"] = extract_context_id_from_a2a_message(
                message_data
            )

        logger.debug(f"🔍 Extracted structured A2A message data: {structured_data}")
        return structured_data

    except Exception as e:
        logger.warning(f"Error extracting structured A2A message data: {e}")
        return {"text": str(message_data), "role": "user"}


def extract_context_id_from_a2a_message(message_data: Dict[str, Any]) -> Optional[str]:
    """Extract context_id from A2A message data.

    Args:
        message_data: A2A message dictionary

    Returns:
        Context ID if found, None otherwise
    """
    # Check different possible locations for context_id
    locations = [
        ["message", "contextId"],  # camelCase
        ["message", "context_id"],  # snake_case
        ["contextId"],  # root level camelCase
        ["context_id"],  # root level snake_case
        ["params", "message", "contextId"],  # JSON-RPC nested
        ["params", "message", "context_id"],  # JSON-RPC nested snake_case
    ]

    for path in locations:
        value = message_data
        try:
            for key in path:
                value = value[key]
            if value:
                return str(value)
        except (KeyError, TypeError):
            continue

    return None


def context_aware_agent_call(
    agent: Any,
    message: str,
    a2a_message_data: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> Any:
    """Call agent with context awareness from A2A message data.

    This function extracts the context_id from A2A message data and passes it
    to the context-aware agent for proper session isolation.

    Args:
        agent: Context-aware agent instance
        message: Message content
        a2a_message_data: Full A2A message data (optional)
        **kwargs: Additional arguments

    Returns:
        Agent response
    """
    context_id = None
    structured_data = {}

    if a2a_message_data:
        # Extract structured message data including context_id
        structured_data = extract_structured_message_data_from_a2a(a2a_message_data)
        context_id = structured_data.get("contextId")

        # Use structured text if available, otherwise use provided message
        if structured_data.get("text") and not message:
            message = structured_data["text"]

        if context_id:
            logger.debug(f"🔑 Extracted context_id: {context_id}")

        # Log additional structured data
        if structured_data.get("messageId"):
            logger.debug(f"📧 Message ID: {structured_data['messageId']}")
        if structured_data.get("taskId"):
            logger.debug(f"📋 Task ID: {structured_data['taskId']}")

    # Call agent with context_id if it supports it
    if hasattr(agent, "_context_aware_wrapper"):
        return agent(message, context_id=context_id, **kwargs)
    else:
        logger.warning("Agent does not support context isolation")
        return agent(message, **kwargs)
