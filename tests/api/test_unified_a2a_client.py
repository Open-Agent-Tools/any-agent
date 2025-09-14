"""Tests for unified A2A client helper."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from any_agent.api.unified_a2a_client_helper import UnifiedA2AClientHelper


class TestUnifiedA2AClientHelper:
    """Test unified A2A client helper functionality."""

    def test_init(self):
        """Test UnifiedA2AClientHelper initialization."""
        client = UnifiedA2AClientHelper(timeout=60)
        assert client.timeout == 60

    def test_init_default_timeout(self):
        """Test UnifiedA2AClientHelper with default timeout."""
        client = UnifiedA2AClientHelper()
        assert client.timeout == 30

    @pytest.mark.asyncio
    async def test_missing_a2a_sdk(self):
        """Test behavior when a2a-sdk is not available."""
        with patch('any_agent.api.unified_a2a_client_helper.A2A_SDK_AVAILABLE', False):
            client = UnifiedA2AClientHelper()
            
            # Should raise ImportError for get_agent_info
            with pytest.raises(ImportError, match="a2a-sdk not available"):
                await client.get_agent_info("http://localhost:8080")
            
            # Should raise ImportError for send_message
            with pytest.raises(ImportError, match="a2a-sdk not available"):
                await client.send_message("http://localhost:8080", "test message")

    @pytest.mark.asyncio
    async def test_get_agent_info_success(self):
        """Test successful agent info retrieval."""
        client = UnifiedA2AClientHelper()
        
        mock_agent_card = MagicMock()
        mock_agent_card.name = "Test Agent"
        mock_agent_card.description = "A test agent"
        mock_agent_card.protocol_version = "1.0"
        
        mock_resolver = MagicMock()
        mock_resolver.get_agent_card = AsyncMock(return_value=mock_agent_card)
        
        with patch('any_agent.api.unified_a2a_client_helper.A2ACardResolver', return_value=mock_resolver):
            with patch('any_agent.api.unified_a2a_client_helper.httpx.AsyncClient'):
                result = await client.get_agent_info("http://localhost:8080")
        
        assert result["name"] == "Test Agent"
        assert result["description"] == "A test agent"
        assert result["protocol_version"] == "1.0"
        assert result["card"] is mock_agent_card

    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """Test successful message sending."""
        client = UnifiedA2AClientHelper()
        
        # Mock the entire client creation chain
        mock_agent_card = MagicMock()
        mock_agent_card.name = "Test Agent"
        
        mock_a2a_client = MagicMock()
        mock_a2a_client.close = AsyncMock()
        
        # Mock message response with model_dump method
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "artifacts": [{
                "parts": [{"text": "Hello! I'm a test response."}]
            }]
        }
        
        async def mock_message_iterator():
            yield mock_response
        
        mock_a2a_client.send_message = MagicMock(return_value=mock_message_iterator())
        
        # Mock client creation method
        async def mock_create_client(base_url, httpx_client):
            return mock_a2a_client, mock_agent_card
        
        client._create_a2a_client = mock_create_client
        
        with patch('any_agent.api.unified_a2a_client_helper.create_text_message_object') as mock_create_msg:
            with patch('any_agent.api.unified_a2a_client_helper.Role') as mock_role:
                with patch('any_agent.api.unified_a2a_client_helper.httpx.AsyncClient'):
                    mock_create_msg.return_value = "test message"
                    mock_role.user = "user"
                    
                    result = await client.send_message("http://localhost:8080", "Hello!")
        
        assert len(result) == 1
        assert result[0] == "Hello! I'm a test response."
        mock_a2a_client.close.assert_called_once()

    def test_extract_response_content_artifacts(self):
        """Test response content extraction from artifacts."""
        client = UnifiedA2AClientHelper()
        
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "artifacts": [{
                "parts": [{"text": "Response from artifacts"}]
            }]
        }
        
        result = client._extract_response_content(mock_response)
        assert result == "Response from artifacts"

    def test_extract_response_content_direct_parts(self):
        """Test response content extraction from direct parts."""
        client = UnifiedA2AClientHelper()
        
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "parts": [{"text": "Direct response"}]
        }
        
        result = client._extract_response_content(mock_response)
        assert result == "Direct response"

    def test_extract_response_content_tuple(self):
        """Test response content extraction from tuple responses."""
        client = UnifiedA2AClientHelper()
        
        mock_task = MagicMock()
        mock_artifact = MagicMock()
        mock_artifact.content = "Task artifact content"
        mock_task.artifacts = [mock_artifact]
        
        tuple_response = (mock_task,)
        
        result = client._extract_response_content(tuple_response)
        assert result == "Task artifact content"

    def test_extract_response_content_string(self):
        """Test response content extraction from string responses."""
        client = UnifiedA2AClientHelper()
        
        result = client._extract_response_content("Direct string response")
        assert result == "Direct string response"

    def test_extract_response_content_fallback(self):
        """Test response content extraction fallback."""
        client = UnifiedA2AClientHelper()
        
        class CustomResponse:
            def __init__(self, name):
                self.__class__.__name__ = name
        
        result = client._extract_response_content(CustomResponse("CustomType"))
        assert result == "Response: CustomType"

    def test_is_available_true(self):
        """Test is_available returns True when SDK available."""
        with patch('any_agent.api.unified_a2a_client_helper.A2A_SDK_AVAILABLE', True):
            assert UnifiedA2AClientHelper.is_available() is True

    def test_is_available_false(self):
        """Test is_available returns False when SDK not available."""
        with patch('any_agent.api.unified_a2a_client_helper.A2A_SDK_AVAILABLE', False):
            assert UnifiedA2AClientHelper.is_available() is False