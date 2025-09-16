"""Chat API handler for web interface A2A communication."""

import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """Chat message structure."""

    id: str
    content: str
    sender: str  # 'user' or 'agent'
    timestamp: str
    message_type: str = "text"  # text, error, system


@dataclass
class ChatSession:
    """Chat session state."""

    session_id: str
    agent_url: str
    agent_name: Optional[str] = None
    is_connected: bool = False
    messages: List[ChatMessage] = field(default_factory=list)


class A2AChatHandler:
    """Handler for A2A chat communication via web interface."""

    def __init__(self, timeout: int = 30):
        """Initialize chat handler.

        Args:
            timeout: Timeout for A2A operations
        """
        self.timeout = timeout
        self.sessions: Dict[str, ChatSession] = {}
        self.a2a_client = self._create_a2a_client()

    def _create_a2a_client(self) -> Union[Any, None]:
        """Create unified A2A client using official a2a-sdk patterns.

        Returns:
            Unified A2A client helper or None if unavailable
        """
        try:
            from .unified_a2a_client_helper import UnifiedA2AClientHelper

            if UnifiedA2AClientHelper.is_available():
                logger.info(
                    "Initializing unified A2A client using official a2a-sdk patterns"
                )
                return UnifiedA2AClientHelper(timeout=self.timeout)
            else:
                logger.warning(
                    "a2a-sdk not available - install with: pip install a2a-sdk>=0.1.0"
                )
                return None

        except ImportError as e:
            logger.error(f"Failed to import unified A2A client: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize unified A2A client: {e}")
            return None

    async def create_session(self, session_id: str, agent_url: str) -> Dict[str, Any]:
        """Create new chat session and attempt A2A connection.

        Args:
            session_id: Unique session identifier
            agent_url: URL of the A2A agent to connect to

        Returns:
            Session creation result with connection status
        """
        if not self.a2a_client:
            return {
                "success": False,
                "error": "No A2A client available - install with: pip install a2a-sdk>=0.1.0",
                "session": None,
            }

        logger.info(f"Creating chat session {session_id} for agent {agent_url}")

        session = ChatSession(session_id=session_id, agent_url=agent_url)

        try:
            # Get agent info using framework-specific client
            agent_info = await self.a2a_client.get_agent_info(agent_url)

            # Update session with agent info
            session.agent_name = agent_info.get("name", "Unknown Agent")
            session.is_connected = True

            # Store session
            self.sessions[session_id] = session

            # No automatic welcome message - start with empty chat

            return {
                "success": True,
                "session": {
                    "session_id": session.session_id,
                    "agent_name": session.agent_name,
                    "agent_url": session.agent_url,
                    "is_connected": session.is_connected,
                    "messages": [asdict(msg) for msg in session.messages],
                },
            }

        except Exception as e:
            logger.error(f"Failed to create chat session: {e}")
            session.is_connected = False
            self.sessions[session_id] = session

            error_msg = ChatMessage(
                id=f"msg_{len(session.messages)}",
                content=f"Failed to connect to agent: {str(e)}",
                sender="agent",
                timestamp=self._get_timestamp(),
                message_type="error",
            )
            session.messages.append(error_msg)

            return {
                "success": False,
                "error": str(e),
                "session": {
                    "session_id": session.session_id,
                    "agent_name": session.agent_name,
                    "agent_url": session.agent_url,
                    "is_connected": session.is_connected,
                    "messages": [asdict(msg) for msg in session.messages],
                },
            }

    async def send_message(
        self, session_id: str, message_content: str
    ) -> Dict[str, Any]:
        """Send message to agent and get response.

        Args:
            session_id: Session identifier
            message_content: User message content

        Returns:
            Message sending result with agent responses
        """
        if session_id not in self.sessions:
            return {"success": False, "error": "Session not found", "messages": []}

        session = self.sessions[session_id]

        if not session.is_connected:
            return {
                "success": False,
                "error": "Session not connected to agent",
                "messages": [],
            }

        if not self.a2a_client:
            return {
                "success": False,
                "error": "No A2A client available - install with: pip install a2a-sdk>=0.1.0",
                "messages": [],
            }

        # Add user message to session
        user_msg = ChatMessage(
            id=f"msg_{len(session.messages)}",
            content=message_content,
            sender="user",
            timestamp=self._get_timestamp(),
        )
        session.messages.append(user_msg)

        try:
            # Prepare context for multi-turn conversation
            context_id = session.session_id  # Use session ID as context ID
            parent_message_id = None
            reference_task_ids: list[str] = []

            # Set parent_message_id to the last message in the session (if any)
            if (
                len(session.messages) > 1
            ):  # > 1 because we just added current user message
                prev_msg = session.messages[
                    -2
                ]  # Previous message (before current user message)
                parent_message_id = prev_msg.id

            # Extract task IDs from previous agent responses (if available)
            # Note: This would require storing task_id in ChatMessage when received
            # For now, we'll pass empty reference_task_ids and rely on contextId

            # Send message using unified A2A client with context preservation
            agent_responses = await self.a2a_client.send_message(
                session.agent_url,
                message_content,
                context_id=context_id,
                reference_task_ids=reference_task_ids if reference_task_ids else None,
                parent_message_id=parent_message_id,
            )

            # Add agent responses to session
            new_messages = []
            for response_text in agent_responses:
                agent_msg = ChatMessage(
                    id=f"msg_{len(session.messages)}",
                    content=response_text,
                    sender="agent",
                    timestamp=self._get_timestamp(),
                )
                session.messages.append(agent_msg)
                new_messages.append(asdict(agent_msg))

            # If no responses, add a default message
            if not agent_responses:
                default_msg = ChatMessage(
                    id=f"msg_{len(session.messages)}",
                    content="I received your message but didn't generate a text response.",
                    sender="agent",
                    timestamp=self._get_timestamp(),
                    message_type="system",
                )
                session.messages.append(default_msg)
                new_messages.append(asdict(default_msg))

            return {
                "success": True,
                "messages": new_messages,
                "user_message": asdict(user_msg),
            }

        except Exception as e:
            logger.error(f"Failed to send message: {e}")

            error_msg = ChatMessage(
                id=f"msg_{len(session.messages)}",
                content=f"Error sending message: {str(e)}",
                sender="agent",
                timestamp=self._get_timestamp(),
                message_type="error",
            )
            session.messages.append(error_msg)

            return {
                "success": False,
                "error": str(e),
                "messages": [asdict(error_msg)],
                "user_message": asdict(user_msg),
            }

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data.

        Args:
            session_id: Session identifier

        Returns:
            Session data or None if not found
        """
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        return {
            "session_id": session.session_id,
            "agent_name": session.agent_name,
            "agent_url": session.agent_url,
            "is_connected": session.is_connected,
            "messages": [asdict(msg) for msg in session.messages],
        }

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions.

        Returns:
            List of session summaries
        """
        return [
            {
                "session_id": session.session_id,
                "agent_name": session.agent_name,
                "agent_url": session.agent_url,
                "is_connected": session.is_connected,
                "message_count": len(session.messages),
            }
            for session in self.sessions.values()
        ]

    def _get_timestamp(self) -> str:
        """Get current timestamp string.

        Returns:
            ISO format timestamp
        """
        from datetime import datetime

        return datetime.now().isoformat()

    def cleanup_session(self, session_id: str) -> Dict[str, Any]:
        """Clean up session and free resources.

        Args:
            session_id: Session identifier to clean up

        Returns:
            Cleanup result with status information
        """
        if session_id not in self.sessions:
            return {
                "success": True,
                "message": "Session not found (already cleaned up)",
                "session_id": session_id,
            }

        session = self.sessions[session_id]

        try:
            # Clean up A2A client connections if possible
            if self.a2a_client and hasattr(self.a2a_client, "cleanup_session"):
                try:
                    self.a2a_client.cleanup_session(session_id, session.agent_url)
                except Exception as cleanup_error:
                    logger.warning(
                        f"A2A client cleanup failed for session {session_id}: {cleanup_error}"
                    )

            # Remove session from memory
            del self.sessions[session_id]

            logger.info(f"Session {session_id} cleaned up successfully")

            return {
                "success": True,
                "message": "Session cleaned up successfully",
                "session_id": session_id,
                "message_count": len(session.messages),
            }

        except Exception as e:
            logger.error(f"Failed to cleanup session {session_id}: {e}")
            return {
                "success": False,
                "error": f"Cleanup failed: {str(e)}",
                "session_id": session_id,
            }

    async def cancel_task(self, session_id: str) -> Dict[str, Any]:
        """Cancel an ongoing task for the specified session.

        Args:
            session_id: Session identifier for the task to cancel

        Returns:
            Cancellation result with status information
        """
        if session_id not in self.sessions:
            return {
                "success": False,
                "error": "Session not found",
                "session_id": session_id,
            }

        session = self.sessions[session_id]

        if not session.is_connected:
            return {
                "success": False,
                "error": "Session not connected to agent",
                "session_id": session_id,
            }

        if not self.a2a_client:
            return {
                "success": False,
                "error": "No A2A client available - install with: pip install a2a-sdk>=0.1.0",
                "session_id": session_id,
            }

        try:
            # Use unified A2A client to send cancel request
            cancel_result = await self.a2a_client.cancel_task(
                session.agent_url, session_id
            )

            # Add cancellation message to session
            cancel_msg = ChatMessage(
                id=f"msg_{len(session.messages)}",
                content="Task cancellation requested",
                sender="agent",
                timestamp=self._get_timestamp(),
                message_type="system",
            )
            session.messages.append(cancel_msg)

            logger.info(f"Task cancelled for session {session_id}")

            return {
                "success": True,
                "message": "Task cancellation requested successfully",
                "session_id": session_id,
                "cancel_result": cancel_result,
                "system_message": asdict(cancel_msg),
            }

        except Exception as e:
            logger.error(f"Failed to cancel task for session {session_id}: {e}")

            error_msg = ChatMessage(
                id=f"msg_{len(session.messages)}",
                content=f"Error cancelling task: {str(e)}",
                sender="agent",
                timestamp=self._get_timestamp(),
                message_type="error",
            )
            session.messages.append(error_msg)

            return {
                "success": False,
                "error": str(e),
                "session_id": session_id,
                "error_message": asdict(error_msg),
            }

    def is_available(self) -> bool:
        """Check if A2A chat is available.

        Returns:
            True if any A2A client is available
        """
        return self.a2a_client is not None
