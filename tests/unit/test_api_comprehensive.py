"""Comprehensive API test suite for chat handlers and helpers."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from any_agent.api.chat_handler import A2AChatHandler, ChatMessage, ChatSession


class TestA2AChatHandler:
    """Test A2A chat handler functionality."""

    def test_init_without_client(self):
        """Test handler initialization when A2A client is not available."""
        with patch(
            "any_agent.api.chat_handler.A2AChatHandler._create_a2a_client",
            return_value=None,
        ):
            handler = A2AChatHandler(timeout=60)
            assert handler.timeout == 60
            assert handler.a2a_client is None
            assert not handler.is_available()

    def test_init_with_client(self):
        """Test handler initialization with A2A client available."""
        mock_client = Mock()
        with patch(
            "any_agent.api.chat_handler.A2AChatHandler._create_a2a_client",
            return_value=mock_client,
        ):
            handler = A2AChatHandler(timeout=30)
            assert handler.timeout == 30
            assert handler.a2a_client is mock_client
            assert handler.is_available()

    @pytest.mark.asyncio
    async def test_create_session_no_client(self):
        """Test session creation when no A2A client is available."""
        with patch(
            "any_agent.api.chat_handler.A2AChatHandler._create_a2a_client",
            return_value=None,
        ):
            handler = A2AChatHandler()
            result = await handler.create_session(
                "test-session", "http://localhost:8080"
            )

            assert not result["success"]
            assert "No A2A client available" in result["error"]
            assert result["session"] is None

    @pytest.mark.asyncio
    async def test_create_session_success(self):
        """Test successful session creation."""
        mock_client = AsyncMock()
        mock_client.get_agent_info.return_value = {"name": "Test Agent"}

        with patch(
            "any_agent.api.chat_handler.A2AChatHandler._create_a2a_client",
            return_value=mock_client,
        ):
            handler = A2AChatHandler()
            result = await handler.create_session(
                "test-session", "http://localhost:8080"
            )

            assert result["success"]
            assert result["session"]["session_id"] == "test-session"
            assert result["session"]["agent_name"] == "Test Agent"
            assert result["session"]["is_connected"]

    @pytest.mark.asyncio
    async def test_create_session_failure(self):
        """Test session creation failure."""
        mock_client = AsyncMock()
        mock_client.get_agent_info.side_effect = Exception("Connection failed")

        with patch(
            "any_agent.api.chat_handler.A2AChatHandler._create_a2a_client",
            return_value=mock_client,
        ):
            handler = A2AChatHandler()
            result = await handler.create_session(
                "test-session", "http://localhost:8080"
            )

            assert not result["success"]
            assert "Connection failed" in result["error"]
            assert not result["session"]["is_connected"]
            assert len(result["session"]["messages"]) == 1  # Error message added

    @pytest.mark.asyncio
    async def test_send_message_no_session(self):
        """Test sending message to non-existent session."""
        handler = A2AChatHandler()
        result = await handler.send_message("invalid-session", "Hello")

        assert not result["success"]
        assert "Session not found" in result["error"]

    @pytest.mark.asyncio
    async def test_send_message_not_connected(self):
        """Test sending message when session not connected."""
        handler = A2AChatHandler()
        handler.sessions["test-session"] = ChatSession(
            session_id="test-session",
            agent_url="http://localhost:8080",
            is_connected=False,
        )

        result = await handler.send_message("test-session", "Hello")

        assert not result["success"]
        assert "Session not connected" in result["error"]

    @pytest.mark.asyncio
    async def test_send_message_no_client(self):
        """Test sending message when no A2A client available."""
        with patch(
            "any_agent.api.chat_handler.A2AChatHandler._create_a2a_client",
            return_value=None,
        ):
            handler = A2AChatHandler()
            handler.sessions["test-session"] = ChatSession(
                session_id="test-session",
                agent_url="http://localhost:8080",
                is_connected=True,
            )

            result = await handler.send_message("test-session", "Hello")

            assert not result["success"]
            assert "No A2A client available" in result["error"]

    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """Test successful message sending."""
        mock_client = AsyncMock()
        mock_client.send_message.return_value = ["Agent response"]

        with patch(
            "any_agent.api.chat_handler.A2AChatHandler._create_a2a_client",
            return_value=mock_client,
        ):
            handler = A2AChatHandler()
            handler.sessions["test-session"] = ChatSession(
                session_id="test-session",
                agent_url="http://localhost:8080",
                is_connected=True,
            )

            result = await handler.send_message("test-session", "Hello")

            assert result["success"]
            assert len(result["messages"]) == 1
            assert result["messages"][0]["content"] == "Agent response"
            assert result["user_message"]["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_send_message_no_response(self):
        """Test message sending with no agent response."""
        mock_client = AsyncMock()
        mock_client.send_message.return_value = []

        with patch(
            "any_agent.api.chat_handler.A2AChatHandler._create_a2a_client",
            return_value=mock_client,
        ):
            handler = A2AChatHandler()
            handler.sessions["test-session"] = ChatSession(
                session_id="test-session",
                agent_url="http://localhost:8080",
                is_connected=True,
            )

            result = await handler.send_message("test-session", "Hello")

            assert result["success"]
            assert len(result["messages"]) == 1
            assert "didn't generate a text response" in result["messages"][0]["content"]

    @pytest.mark.asyncio
    async def test_send_message_with_context(self):
        """Test message sending with conversation context."""
        mock_client = AsyncMock()
        mock_client.send_message.return_value = ["Response with context"]

        with patch(
            "any_agent.api.chat_handler.A2AChatHandler._create_a2a_client",
            return_value=mock_client,
        ):
            handler = A2AChatHandler()
            session = ChatSession(
                session_id="test-session",
                agent_url="http://localhost:8080",
                is_connected=True,
            )
            # Add previous message
            session.messages.append(
                ChatMessage(
                    id="msg_0",
                    content="Previous message",
                    sender="user",
                    timestamp="2023-01-01T00:00:00",
                )
            )
            handler.sessions["test-session"] = session

            result = await handler.send_message("test-session", "Follow-up message")

            assert result["success"]
            # Should pass parent_message_id in context
            mock_client.send_message.assert_called_with(
                "http://localhost:8080",
                "Follow-up message",
                context_id="test-session",
                reference_task_ids=None,
                parent_message_id="msg_0",
            )

    @pytest.mark.asyncio
    async def test_send_message_error(self):
        """Test message sending error handling."""
        mock_client = AsyncMock()
        mock_client.send_message.side_effect = Exception("Send error")

        with patch(
            "any_agent.api.chat_handler.A2AChatHandler._create_a2a_client",
            return_value=mock_client,
        ):
            handler = A2AChatHandler()
            handler.sessions["test-session"] = ChatSession(
                session_id="test-session",
                agent_url="http://localhost:8080",
                is_connected=True,
            )

            result = await handler.send_message("test-session", "Hello")

            assert not result["success"]
            assert "Send error" in result["error"]
            assert len(result["messages"]) == 1  # Error message
            assert "Error sending message" in result["messages"][0]["content"]

    def test_get_session_exists(self):
        """Test getting existing session."""
        handler = A2AChatHandler()
        session = ChatSession(
            session_id="test-session",
            agent_url="http://localhost:8080",
            agent_name="Test Agent",
            is_connected=True,
        )
        handler.sessions["test-session"] = session

        result = handler.get_session("test-session")

        assert result is not None
        assert result["session_id"] == "test-session"
        assert result["agent_name"] == "Test Agent"
        assert result["is_connected"]

    def test_get_session_not_exists(self):
        """Test getting non-existent session."""
        handler = A2AChatHandler()
        result = handler.get_session("invalid-session")
        assert result is None

    def test_list_sessions_empty(self):
        """Test listing sessions when none exist."""
        handler = A2AChatHandler()
        result = handler.list_sessions()
        assert result == []

    def test_list_sessions_multiple(self):
        """Test listing multiple sessions."""
        handler = A2AChatHandler()
        session1 = ChatSession(
            session_id="session1",
            agent_url="http://localhost:8080",
            agent_name="Agent 1",
        )
        session2 = ChatSession(
            session_id="session2",
            agent_url="http://localhost:8081",
            agent_name="Agent 2",
        )
        handler.sessions["session1"] = session1
        handler.sessions["session2"] = session2

        result = handler.list_sessions()

        assert len(result) == 2
        assert any(s["session_id"] == "session1" for s in result)
        assert any(s["session_id"] == "session2" for s in result)

    def test_get_timestamp(self):
        """Test timestamp generation."""
        handler = A2AChatHandler()
        timestamp = handler._get_timestamp()

        assert isinstance(timestamp, str)
        # Should be in ISO format
        assert "T" in timestamp


class TestChatMessage:
    """Test ChatMessage dataclass."""

    def test_chat_message_creation(self):
        """Test creating a chat message."""
        msg = ChatMessage(
            id="msg_1",
            content="Hello world",
            sender="user",
            timestamp="2023-01-01T00:00:00",
            message_type="text",
        )

        assert msg.id == "msg_1"
        assert msg.content == "Hello world"
        assert msg.sender == "user"
        assert msg.timestamp == "2023-01-01T00:00:00"
        assert msg.message_type == "text"

    def test_chat_message_default_type(self):
        """Test chat message with default type."""
        msg = ChatMessage(
            id="msg_1", content="Hello", sender="user", timestamp="2023-01-01T00:00:00"
        )

        assert msg.message_type == "text"


class TestChatSession:
    """Test ChatSession dataclass."""

    def test_chat_session_creation(self):
        """Test creating a chat session."""
        session = ChatSession(session_id="session_1", agent_url="http://localhost:8080")

        assert session.session_id == "session_1"
        assert session.agent_url == "http://localhost:8080"
        assert session.agent_name is None
        assert not session.is_connected
        assert session.messages == []

    def test_chat_session_with_messages(self):
        """Test chat session with messages."""
        msg = ChatMessage(
            id="msg_1", content="Hello", sender="user", timestamp="2023-01-01T00:00:00"
        )
        session = ChatSession(
            session_id="session_1", agent_url="http://localhost:8080", messages=[msg]
        )

        assert len(session.messages) == 1
        assert session.messages[0].content == "Hello"
