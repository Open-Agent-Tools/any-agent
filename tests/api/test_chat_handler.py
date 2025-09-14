"""Tests for A2A chat handler session management and cleanup."""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from any_agent.api.chat_handler import A2AChatHandler, ChatMessage, ChatSession


class TestA2AChatHandler:
    """Test suite for A2AChatHandler focusing on session cleanup functionality."""

    @pytest.fixture
    def mock_a2a_client(self):
        """Create mock A2A client."""
        mock_client = Mock()
        mock_client.get_agent_info = AsyncMock(
            return_value={"name": "Test Agent", "status": "active"}
        )
        mock_client.send_message = AsyncMock(return_value=["Test response"])
        mock_client.cleanup_session = Mock()
        return mock_client

    @pytest.fixture
    def chat_handler(self, mock_a2a_client):
        """Create chat handler with mocked A2A client."""
        with patch(
            "any_agent.api.chat_handler.A2AChatHandler._create_a2a_client"
        ) as mock_create:
            mock_create.return_value = mock_a2a_client
            handler = A2AChatHandler(timeout=30)
            return handler

    def test_cleanup_session_success(self, chat_handler, mock_a2a_client):
        """Test successful session cleanup."""
        # Setup: Create a session
        session_id = "test_session_123"
        agent_url = "http://localhost:8080"

        session = ChatSession(
            session_id=session_id,
            agent_url=agent_url,
            agent_name="Test Agent",
            is_connected=True,
            messages=[
                ChatMessage(
                    id="msg_1",
                    content="Hello",
                    sender="user",
                    timestamp="2024-01-01T00:00:00",
                )
            ],
        )
        chat_handler.sessions[session_id] = session

        # Execute: Cleanup session
        result = chat_handler.cleanup_session(session_id)

        # Verify: Session cleaned up successfully
        assert result["success"] is True
        assert result["session_id"] == session_id
        assert result["message"] == "Session cleaned up successfully"
        assert result["message_count"] == 1
        assert session_id not in chat_handler.sessions

        # Verify: A2A client cleanup was called
        mock_a2a_client.cleanup_session.assert_called_once_with(session_id, agent_url)

    def test_cleanup_session_not_found(self, chat_handler):
        """Test cleanup of non-existent session."""
        session_id = "nonexistent_session"

        # Execute: Cleanup non-existent session
        result = chat_handler.cleanup_session(session_id)

        # Verify: Returns success with appropriate message
        assert result["success"] is True
        assert result["session_id"] == session_id
        assert result["message"] == "Session not found (already cleaned up)"

    def test_cleanup_session_a2a_client_error(self, chat_handler, mock_a2a_client):
        """Test session cleanup when A2A client cleanup fails."""
        # Setup: Create session and mock A2A client failure
        session_id = "test_session_456"
        agent_url = "http://localhost:8080"

        session = ChatSession(
            session_id=session_id,
            agent_url=agent_url,
            agent_name="Test Agent",
            is_connected=True,
        )
        chat_handler.sessions[session_id] = session

        # Mock A2A client cleanup to raise exception
        mock_a2a_client.cleanup_session.side_effect = Exception("A2A cleanup failed")

        # Execute: Cleanup session
        result = chat_handler.cleanup_session(session_id)

        # Verify: Session still cleaned up despite A2A client error
        assert result["success"] is True
        assert result["session_id"] == session_id
        assert session_id not in chat_handler.sessions

    def test_cleanup_session_no_a2a_client_cleanup_method(
        self, chat_handler, mock_a2a_client
    ):
        """Test cleanup when A2A client doesn't have cleanup method."""
        # Setup: Remove cleanup method from mock client
        delattr(mock_a2a_client, "cleanup_session")

        session_id = "test_session_789"
        session = ChatSession(
            session_id=session_id,
            agent_url="http://localhost:8080",
            agent_name="Test Agent",
            is_connected=True,
        )
        chat_handler.sessions[session_id] = session

        # Execute: Cleanup session
        result = chat_handler.cleanup_session(session_id)

        # Verify: Session cleaned up successfully without A2A client cleanup
        assert result["success"] is True
        assert session_id not in chat_handler.sessions

    def test_cleanup_session_general_error(self, chat_handler):
        """Test cleanup when general error occurs."""
        # Setup: Force an error by corrupting session data
        session_id = "error_session"
        chat_handler.sessions[session_id] = (
            "invalid_session_data"  # Not a ChatSession object
        )

        # Execute: Cleanup session
        result = chat_handler.cleanup_session(session_id)

        # Verify: Error handled gracefully
        assert result["success"] is False
        assert "Cleanup failed:" in result["error"]
        assert result["session_id"] == session_id

    @pytest.mark.asyncio
    async def test_new_session_cleanup_workflow(self, chat_handler, mock_a2a_client):
        """Test the complete new session workflow with cleanup."""
        session_id_1 = "session_workflow_1"
        session_id_2 = "session_workflow_2"
        agent_url = "http://localhost:8080"

        # Step 1: Create first session
        result1 = await chat_handler.create_session(session_id_1, agent_url)
        assert result1["success"] is True
        assert session_id_1 in chat_handler.sessions

        # Step 2: Send message to first session
        await chat_handler.send_message(session_id_1, "Hello from session 1")
        assert len(chat_handler.sessions[session_id_1].messages) >= 1

        # Step 3: Create second session (simulating "New" button click)
        result2 = await chat_handler.create_session(session_id_2, agent_url)
        assert result2["success"] is True
        assert session_id_2 in chat_handler.sessions

        # Step 4: Cleanup first session (simulating React UI cleanup call)
        cleanup_result = chat_handler.cleanup_session(session_id_1)
        assert cleanup_result["success"] is True
        assert session_id_1 not in chat_handler.sessions
        assert session_id_2 in chat_handler.sessions  # Second session should remain

        # Step 5: Send message to second session
        result3 = await chat_handler.send_message(session_id_2, "Hello from session 2")
        assert result3["success"] is True

        # Verify: Only second session exists and has fresh context
        assert len(chat_handler.sessions) == 1
        assert session_id_2 in chat_handler.sessions
        session_2 = chat_handler.sessions[session_id_2]

        # Should have user message + agent response
        assert len(session_2.messages) >= 2

    def test_session_isolation_after_cleanup(self, chat_handler):
        """Test that sessions are properly isolated after cleanup."""
        # Create multiple sessions with different contexts
        sessions_data = [
            ("session_isolation_1", "Context from session 1"),
            ("session_isolation_2", "Context from session 2"),
            ("session_isolation_3", "Context from session 3"),
        ]

        # Create sessions with different message histories
        for session_id, context in sessions_data:
            session = ChatSession(
                session_id=session_id,
                agent_url="http://localhost:8080",
                agent_name="Test Agent",
                is_connected=True,
                messages=[
                    ChatMessage(
                        id=f"msg_{session_id}",
                        content=context,
                        sender="user",
                        timestamp="2024-01-01T00:00:00",
                    )
                ],
            )
            chat_handler.sessions[session_id] = session

        # Verify all sessions exist with correct contexts
        assert len(chat_handler.sessions) == 3
        for session_id, expected_context in sessions_data:
            session = chat_handler.sessions[session_id]
            assert session.messages[0].content == expected_context

        # Cleanup middle session
        cleanup_result = chat_handler.cleanup_session("session_isolation_2")
        assert cleanup_result["success"] is True

        # Verify: Other sessions remain with their contexts intact
        assert len(chat_handler.sessions) == 2
        assert "session_isolation_1" in chat_handler.sessions
        assert "session_isolation_3" in chat_handler.sessions
        assert "session_isolation_2" not in chat_handler.sessions

        # Verify contexts remain isolated
        session_1 = chat_handler.sessions["session_isolation_1"]
        session_3 = chat_handler.sessions["session_isolation_3"]
        assert session_1.messages[0].content == "Context from session 1"
        assert session_3.messages[0].content == "Context from session 3"


class TestChatMessage:
    """Test suite for ChatMessage data structure."""

    def test_chat_message_creation(self):
        """Test ChatMessage creation and structure."""
        message = ChatMessage(
            id="test_msg_1",
            content="Hello, world!",
            sender="user",
            timestamp="2024-01-01T00:00:00",
            message_type="text",
        )

        assert message.id == "test_msg_1"
        assert message.content == "Hello, world!"
        assert message.sender == "user"
        assert message.timestamp == "2024-01-01T00:00:00"
        assert message.message_type == "text"

    def test_chat_message_default_message_type(self):
        """Test ChatMessage with default message type."""
        message = ChatMessage(
            id="test_msg_2",
            content="Error occurred",
            sender="agent",
            timestamp="2024-01-01T00:00:00",
        )

        assert message.message_type == "text"  # Default value


class TestChatSession:
    """Test suite for ChatSession data structure."""

    def test_chat_session_creation(self):
        """Test ChatSession creation and structure."""
        session = ChatSession(
            session_id="test_session",
            agent_url="http://localhost:8080",
            agent_name="Test Agent",
            is_connected=True,
            messages=[],
        )

        assert session.session_id == "test_session"
        assert session.agent_url == "http://localhost:8080"
        assert session.agent_name == "Test Agent"
        assert session.is_connected is True
        assert len(session.messages) == 0

    def test_chat_session_default_values(self):
        """Test ChatSession with default values."""
        session = ChatSession(
            session_id="minimal_session", agent_url="http://localhost:8080"
        )

        assert session.agent_name is None
        assert session.is_connected is False
        assert len(session.messages) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
