"""Consolidated context management for agent wrappers.

Eliminates duplication across context wrapper implementations by providing
unified context state management, agent instance handling, and context isolation logic.
"""

import logging
import threading
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ContextState:
    """Represents the state of a context session."""

    context_id: str
    agent_instance: Any
    created_at: float
    last_accessed: float
    message_count: int = 0


class ContextManager:
    """Unified context state management for agent wrappers."""

    def __init__(self):
        """Initialize context manager with thread safety."""
        self.contexts: Dict[str, ContextState] = {}
        self.lock = threading.RLock()

    def get_or_create_context(
        self,
        context_id: Optional[str],
        agent_factory: Callable[[], Any],
        default_context_id: str = "default",
    ) -> tuple[str, Any]:
        """Get existing context or create new one.

        Args:
            context_id: Context identifier (None uses default)
            agent_factory: Factory function to create new agent instances
            default_context_id: Default context ID if none provided

        Returns:
            Tuple of (actual_context_id, agent_instance)
        """
        actual_context_id = context_id or default_context_id

        with self.lock:
            if actual_context_id not in self.contexts:
                # Create new context
                agent_instance = agent_factory()

                import time

                now = time.time()
                self.contexts[actual_context_id] = ContextState(
                    context_id=actual_context_id,
                    agent_instance=agent_instance,
                    created_at=now,
                    last_accessed=now,
                )
                logger.info(
                    f"🔧 Created isolated agent instance for context: {actual_context_id}"
                )
            else:
                # Update access time
                import time

                self.contexts[actual_context_id].last_accessed = time.time()

            context_state = self.contexts[actual_context_id]
            context_state.message_count += 1

            logger.debug(
                f"🎯 Using context: {actual_context_id} (messages: {context_state.message_count})"
            )
            return actual_context_id, context_state.agent_instance

    def cleanup_context(self, context_id: str) -> bool:
        """Remove a context and its agent instance.

        Args:
            context_id: Context to remove

        Returns:
            True if context was removed, False if not found
        """
        with self.lock:
            if context_id in self.contexts:
                del self.contexts[context_id]
                logger.info(f"🧹 Cleaned up context: {context_id}")
                return True
            return False

    def list_contexts(self) -> list[str]:
        """Get list of active context IDs."""
        with self.lock:
            return list(self.contexts.keys())

    def get_context_stats(self) -> dict[str, dict]:
        """Get statistics for all contexts."""
        with self.lock:
            return {
                ctx_id: {
                    "created_at": ctx.created_at,
                    "last_accessed": ctx.last_accessed,
                    "message_count": ctx.message_count,
                }
                for ctx_id, ctx in self.contexts.items()
            }


class BaseContextWrapper(ABC):
    """Abstract base for all context-aware agent wrappers."""

    def __init__(self, agent: Any, init_message: str):
        """Initialize base wrapper.

        Args:
            agent: Original agent instance
            init_message: Logging message for wrapper creation
        """
        self.original_agent = agent
        self.context_manager = ContextManager()
        self.lock = threading.RLock()
        logger.info(init_message)

    @abstractmethod
    def create_agent_instance(self) -> Any:
        """Create new agent instance for context isolation.

        Returns:
            New agent instance with same configuration as original
        """
        pass

    def __call__(self, message: str, context_id: Optional[str] = None, **kwargs) -> Any:
        """Process message with context isolation.

        Args:
            message: Message to process
            context_id: Context identifier for isolation
            **kwargs: Additional arguments

        Returns:
            Agent response
        """
        with self.lock:
            actual_context_id, agent_instance = (
                self.context_manager.get_or_create_context(
                    context_id, self.create_agent_instance
                )
            )
            return agent_instance(message, **kwargs)

    def __getattr__(self, name):
        """Delegate attribute access to original agent."""
        return getattr(self.original_agent, name)

    def cleanup_context(self, context_id: str) -> bool:
        """Clean up specific context."""
        return self.context_manager.cleanup_context(context_id)

    def get_context_stats(self) -> dict:
        """Get context statistics."""
        return self.context_manager.get_context_stats()


class SessionManagedWrapper(BaseContextWrapper):
    """Wrapper for agents with built-in session management."""

    def create_agent_instance(self) -> Any:
        """Return original agent (no copying needed for session-managed agents)."""
        return self.original_agent

    def __call__(self, message: str, context_id: Optional[str] = None, **kwargs) -> Any:
        """Use built-in session management instead of instance isolation."""
        if context_id and hasattr(self.original_agent, "session_manager"):
            # Try to use built-in session management
            session_manager = self.original_agent.session_manager
            if hasattr(session_manager, "session_id"):
                original_session = getattr(session_manager, "session_id", None)
                try:
                    session_manager.session_id = context_id
                    return self.original_agent(message, **kwargs)
                finally:
                    # Restore original session
                    if original_session:
                        session_manager.session_id = original_session

        # Fallback to direct call
        return self.original_agent(message, **kwargs)


class GenericContextWrapper(BaseContextWrapper):
    """Wrapper for generic agents requiring instance copying."""

    def create_agent_instance(self) -> Any:
        """Create copy of original agent with comprehensive attribute preservation."""
        try:
            agent_class = self.original_agent.__class__
            kwargs = {}

            # Comprehensive attribute discovery
            for attr_name in dir(self.original_agent):
                if not attr_name.startswith("_") and not callable(
                    getattr(self.original_agent, attr_name, None)
                ):
                    try:
                        attr_value = getattr(self.original_agent, attr_name)
                        # Skip complex objects that likely aren't constructor parameters
                        if not isinstance(attr_value, (type, type(None))):
                            kwargs[attr_name] = attr_value
                    except Exception:
                        continue

            # Ensure critical instruction attributes are preserved
            instruction_attrs = [
                "instruction",
                "instructions",
                "system_prompt",
                "agent_instruction",
                "agent_instructions",
                "SYSTEM_PROMPT",
                "INSTRUCTION",
                "INSTRUCTIONS",
                "prompt",
                "PROMPT",
                "system_message",
                "agent_prompt",
                "AGENT_PROMPT",
            ]

            for attr in instruction_attrs:
                if hasattr(self.original_agent, attr):
                    kwargs[attr] = getattr(self.original_agent, attr)

            return agent_class(**kwargs)

        except Exception as e:
            logger.debug(f"Failed to copy agent with all attributes: {e}")

            # Fallback: try with only critical attributes
            try:
                agent_class = self.original_agent.__class__
                critical_kwargs = {}

                essential_attrs = [
                    "model",
                    "name",
                    "description",
                    "tools",
                    "instruction",
                    "system_prompt",
                    "agent_instruction",
                ]

                for attr in essential_attrs:
                    if hasattr(self.original_agent, attr):
                        critical_kwargs[attr] = getattr(self.original_agent, attr)

                return agent_class(**critical_kwargs)

            except Exception as fallback_error:
                logger.warning(
                    f"Could not create agent copy even with fallback: {fallback_error}. "
                    "Using shared instance (may cause context bleeding)"
                )
                return self.original_agent


def create_context_wrapper(agent: Any, agent_type: str) -> BaseContextWrapper:
    """Factory function to create appropriate context wrapper.

    Args:
        agent: Original agent instance
        agent_type: Type of agent framework

    Returns:
        Appropriate context wrapper instance
    """
    if agent_type == "strands":
        # Check if agent has session management
        if hasattr(agent, "session_manager") and agent.session_manager is not None:
            return SessionManagedWrapper(
                agent,
                "🔧 Using Strands built-in session management for context isolation",
            )
        else:
            return SessionManagedWrapper(
                agent, "🔧 Using direct agent calls - MCP client sessions preserved"
            )
    else:
        # Generic approach for other frameworks
        return GenericContextWrapper(
            agent,
            f"🔧 Created generic context-aware wrapper for {type(agent).__name__}",
        )
