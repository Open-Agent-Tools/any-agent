"""Tests for A2A validation client."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import httpx
import json
import asyncio

from any_agent.validation.client import A2AValidationClient, A2AValidationConfig, A2AValidationResult
from any_agent.validation.validator import ValidationResult


class TestA2AValidationConfig:
    """Test A2AValidationConfig data class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = A2AValidationConfig(endpoint="http://localhost:8080")
        assert config.endpoint == "http://localhost:8080"
        assert config.timeout == 30.0
        assert config.max_retries == 3
        assert config.auth_token is None
        assert config.auth_type == "bearer"
        assert config.verify_ssl is True
        assert config.headers == {}
    
    def test_custom_config(self):
        """Test custom configuration values."""
        headers = {"User-Agent": "Test"}
        config = A2AValidationConfig(
            endpoint="https://api.example.com",
            timeout=60.0,
            max_retries=5,
            auth_token="secret",
            auth_type="api_key",
            verify_ssl=False,
            headers=headers
        )
        assert config.endpoint == "https://api.example.com"
        assert config.timeout == 60.0
        assert config.max_retries == 5
        assert config.auth_token == "secret"
        assert config.auth_type == "api_key"
        assert config.verify_ssl is False
        assert config.headers == headers


class TestA2AValidationResult:
    """Test A2AValidationResult data class."""
    
    def test_test_result_creation(self):
        """Test creating A2AValidationResult."""
        validation_result = ValidationResult(is_valid=True, errors=[], warnings=[])
        result = A2AValidationResult(
            method="a2a.ping",
            params=None,
            response={"jsonrpc": "2.0", "result": "pong", "id": 1},
            validation_result=validation_result,
            response_time_ms=15.5,
            status_code=200
        )
        
        assert result.method == "a2a.ping"
        assert result.params is None
        assert result.response["result"] == "pong"
        assert result.validation_result.is_valid
        assert result.response_time_ms == 15.5
        assert result.error is None
        assert result.status_code == 200


class TestA2AValidationClient:
    """Test A2A test client functionality."""
    
    def test_init(self):
        """Test A2AValidationClient initialization."""
        config = A2AValidationConfig(endpoint="http://localhost:8080")
        client = A2AValidationClient(config)
        
        assert client.config == config
        assert client._request_id == 0
        assert client.jsonrpc_validator is not None
        assert client.a2a_validator is not None
    
    def test_init_with_auth_bearer(self):
        """Test A2AValidationClient initialization with bearer auth."""
        config = A2AValidationConfig(
            endpoint="http://localhost:8080",
            auth_token="secret123",
            auth_type="bearer"
        )
        client = A2AValidationClient(config)
        
        # Check that auth was configured (we can't easily inspect headers without mocking)
        assert client.config.auth_token == "secret123"
        assert client.config.auth_type == "bearer"
    
    def test_init_with_auth_api_key(self):
        """Test A2AValidationClient initialization with API key auth."""
        config = A2AValidationConfig(
            endpoint="http://localhost:8080",
            auth_token="api123",
            auth_type="api_key"
        )
        client = A2AValidationClient(config)
        
        assert client.config.auth_token == "api123"
        assert client.config.auth_type == "api_key"
    
    def test_get_next_id(self):
        """Test request ID generation."""
        config = A2AValidationConfig(endpoint="http://localhost:8080")
        client = A2AValidationClient(config)
        
        assert client._get_next_id() == 1
        assert client._get_next_id() == 2
        assert client._get_next_id() == 3
    
    @pytest.mark.asyncio
    async def test_call_method_success(self):
        """Test successful method call."""
        config = A2AValidationConfig(endpoint="http://localhost:8080")
        client = A2AValidationClient(config)
        
        mock_response = httpx.Response(
            200,
            json={"jsonrpc": "2.0", "result": "pong", "id": 1},
            request=httpx.Request("POST", "http://localhost:8080/")
        )
        
        with patch.object(client.client, 'post', return_value=mock_response) as mock_post:
            result = await client.call_method("a2a.ping")
        
        assert result.method == "a2a.ping"
        assert result.response["result"] == "pong"
        assert result.status_code == 200
        assert result.error is None
        assert result.validation_result.is_valid
        
        # Verify the request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"]["method"] == "a2a.ping"
        assert call_args[1]["json"]["jsonrpc"] == "2.0"
    
    @pytest.mark.asyncio 
    async def test_call_method_with_params(self):
        """Test method call with parameters."""
        config = A2AValidationConfig(endpoint="http://localhost:8080")
        client = A2AValidationClient(config)
        
        mock_response = httpx.Response(
            200,
            json={"jsonrpc": "2.0", "result": {"status": "ok"}, "id": 1},
            request=httpx.Request("POST", "http://localhost:8080/")
        )
        
        params = {"arg1": "value1", "arg2": 42}
        
        with patch.object(client.client, 'post', return_value=mock_response) as mock_post:
            result = await client.call_method("a2a.test", params=params)
        
        assert result.method == "a2a.test"
        assert result.params == params
        assert result.response["result"]["status"] == "ok"
        
        # Verify parameters were included in request
        call_args = mock_post.call_args
        assert call_args[1]["json"]["params"] == params
    
    @pytest.mark.asyncio
    async def test_call_method_http_error(self):
        """Test method call with HTTP error."""
        config = A2AValidationConfig(endpoint="http://localhost:8080")
        client = A2AValidationClient(config)
        
        with patch.object(client.client, 'post', side_effect=httpx.ConnectError("Connection failed")):
            result = await client.call_method("a2a.ping")
        
        assert result.method == "a2a.ping"
        assert result.response is None
        assert result.status_code is None
        assert "Connection failed" in result.error
        assert not result.validation_result.is_valid
    
    @pytest.mark.asyncio
    async def test_call_method_invalid_json_response(self):
        """Test method call with invalid JSON response."""
        config = A2AValidationConfig(endpoint="http://localhost:8080")
        client = A2AValidationClient(config)
        
        # Mock response with invalid JSON
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "invalid json"
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "invalid json", 0)
        
        with patch.object(client.client, 'post', return_value=mock_response):
            result = await client.call_method("a2a.ping")
        
        assert result.method == "a2a.ping"
        assert result.response is None
        assert result.status_code == 200
        assert "Invalid JSON" in result.error
        assert not result.validation_result.is_valid
    
    @pytest.mark.asyncio
    async def test_discover_methods(self):
        """Test discover_methods method."""
        config = A2AValidationConfig(endpoint="http://localhost:8080")
        client = A2AValidationClient(config)
        
        methods = ["a2a.ping", "a2a.get_capabilities"]
        mock_response = httpx.Response(
            200,
            json={"jsonrpc": "2.0", "result": methods, "id": 1},
            request=httpx.Request("POST", "http://localhost:8080/")
        )
        
        with patch.object(client.client, 'post', return_value=mock_response):
            result = await client.discover_methods()
        
        assert result.method == "a2a.listMethods"
        assert result.response["result"] == methods
        assert result.validation_result.is_valid
    
    @pytest.mark.asyncio
    async def test_get_agent_card(self):
        """Test get_agent_card method."""
        config = A2AValidationConfig(endpoint="http://localhost:8080")
        client = A2AValidationClient(config)
        
        # Mock the agent card via JSON-RPC call
        agent_card = {
            "name": "Test Agent",
            "version": "1.0.0",
            "capabilities": [
                {
                    "method": "a2a.ping",
                    "description": "Health check method"
                }
            ]
        }
        
        mock_response = httpx.Response(
            200,
            json={"jsonrpc": "2.0", "result": agent_card, "id": 1},
            request=httpx.Request("POST", "http://localhost:8080/")
        )
        
        with patch.object(client.client, 'post', return_value=mock_response):
            result = await client.get_agent_card()
        
        assert result.method == "a2a.getAgentCard"
        assert result.response["result"] == agent_card
        assert result.validation_result.is_valid
    
    @pytest.mark.asyncio
    async def test_validate_endpoint_health(self):
        """Test validate_endpoint_health method."""
        config = A2AValidationConfig(endpoint="http://localhost:8080")
        client = A2AValidationClient(config)
        
        # Mock successful ping response
        mock_response = httpx.Response(
            200,
            json={"jsonrpc": "2.0", "result": "pong", "id": 1},
            request=httpx.Request("POST", "http://localhost:8080/")
        )
        
        with patch.object(client.client, 'post', return_value=mock_response):
            result = await client.validate_endpoint_health()
        
        assert result.method == "a2a.ping"
        assert result.response["result"] == "pong"
        assert result.validation_result.is_valid
        assert result.status_code == 200
    
    @pytest.mark.asyncio
    async def test_batch_call(self):
        """Test batch method calls."""
        config = A2AValidationConfig(endpoint="http://localhost:8080")
        client = A2AValidationClient(config)
        
        methods = [
            {"method": "a2a.ping"},
            {"method": "a2a.test", "params": {"arg": "value"}}
        ]
        
        # Mock individual call_method responses
        ping_result = A2AValidationResult(
            method="a2a.ping",
            params=None,
            response={"jsonrpc": "2.0", "result": "pong", "id": 1},
            validation_result=ValidationResult(is_valid=True, errors=[], warnings=[]),
            response_time_ms=10.0
        )
        
        test_result = A2AValidationResult(
            method="a2a.test",
            params={"arg": "value"},
            response={"jsonrpc": "2.0", "result": "ok", "id": 2},
            validation_result=ValidationResult(is_valid=True, errors=[], warnings=[]),
            response_time_ms=15.0
        )
        
        with patch.object(client, 'call_method', side_effect=[ping_result, test_result]):
            results = await client.batch_call(methods)
        
        assert len(results) == 2
        assert results[0].method == "a2a.ping"
        assert results[1].method == "a2a.test"
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using client as async context manager."""
        config = A2AValidationConfig(endpoint="http://localhost:8080")
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value = AsyncMock()
            async with A2AValidationClient(config) as client:
                assert isinstance(client, A2AValidationClient)