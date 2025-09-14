"""Tests for A2A protocol validators."""

from any_agent.validation.validator import JSONRPCValidator, A2AMessageValidator


class TestJSONRPCValidator:
    """Test JSON-RPC 2.0 message validation."""
    
    def test_valid_request(self) -> None:
        """Test validation of valid JSON-RPC request."""
        validator = JSONRPCValidator()
        message = {
            "jsonrpc": "2.0",
            "method": "a2a.ping",
            "id": 1
        }
        
        result = validator.validate_request(message)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_valid_request_with_params(self) -> None:
        """Test validation of valid JSON-RPC request with parameters."""
        validator = JSONRPCValidator()
        message = {
            "jsonrpc": "2.0",
            "method": "a2a.call",
            "params": {"arg1": "value1"},
            "id": 1
        }
        
        result = validator.validate_request(message)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_invalid_jsonrpc_version(self) -> None:
        """Test validation fails for invalid JSON-RPC version."""
        validator = JSONRPCValidator()
        message = {
            "jsonrpc": "1.0",
            "method": "a2a.ping",
            "id": 1
        }
        
        result = validator.validate_request(message)
        assert not result.is_valid
        assert any("2.0" in error for error in result.errors)
    
    def test_missing_method(self) -> None:
        """Test validation fails for missing method field."""
        validator = JSONRPCValidator()
        message = {
            "jsonrpc": "2.0",
            "id": 1
        }
        
        result = validator.validate_request(message)
        assert not result.is_valid
    
    def test_valid_response_with_result(self) -> None:
        """Test validation of valid JSON-RPC response with result."""
        validator = JSONRPCValidator()
        message = {
            "jsonrpc": "2.0",
            "result": {"status": "ok"},
            "id": 1
        }
        
        result = validator.validate_response(message)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_valid_response_with_error(self) -> None:
        """Test validation of valid JSON-RPC error response."""
        validator = JSONRPCValidator()
        message = {
            "jsonrpc": "2.0",
            "error": {
                "code": -32601,
                "message": "Method not found"
            },
            "id": 1
        }
        
        result = validator.validate_response(message)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_response_with_both_result_and_error(self) -> None:
        """Test validation fails when response has both result and error."""
        validator = JSONRPCValidator()
        message = {
            "jsonrpc": "2.0",
            "result": {"status": "ok"},
            "error": {
                "code": -32601,
                "message": "Method not found"
            },
            "id": 1
        }
        
        result = validator.validate_response(message)
        assert not result.is_valid
        assert any("both" in error.lower() for error in result.errors)
    
    def test_valid_notification(self) -> None:
        """Test validation of valid JSON-RPC notification."""
        validator = JSONRPCValidator()
        message = {
            "jsonrpc": "2.0",
            "method": "a2a.notify"
        }
        
        result = validator.validate_notification(message)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_notification_with_id(self) -> None:
        """Test validation fails for notification with id field."""
        validator = JSONRPCValidator()
        message = {
            "jsonrpc": "2.0",
            "method": "a2a.notify",
            "id": 1
        }
        
        result = validator.validate_notification(message)
        assert not result.is_valid
        assert any("id" in error.lower() for error in result.errors)
    
    def test_auto_detect_request(self) -> None:
        """Test automatic message type detection for request."""
        validator = JSONRPCValidator()
        message = {
            "jsonrpc": "2.0",
            "method": "a2a.ping",
            "id": 1
        }
        
        result = validator.validate_message(message)
        assert result.is_valid
    
    def test_auto_detect_notification(self) -> None:
        """Test automatic message type detection for notification."""
        validator = JSONRPCValidator()
        message = {
            "jsonrpc": "2.0",
            "method": "a2a.notify"
        }
        
        result = validator.validate_message(message)
        assert result.is_valid
    
    def test_auto_detect_response(self) -> None:
        """Test automatic message type detection for response."""
        validator = JSONRPCValidator()
        message = {
            "jsonrpc": "2.0",
            "result": {"status": "ok"},
            "id": 1
        }
        
        result = validator.validate_message(message)
        assert result.is_valid
    
    def test_invalid_json_string(self) -> None:
        """Test validation fails for invalid JSON string."""
        validator = JSONRPCValidator()
        message = '{"jsonrpc": "2.0", "method": "ping"'  # Invalid JSON
        
        result = validator.validate_message(message)
        assert not result.is_valid
        assert any("json" in error.lower() for error in result.errors)


class TestA2AMessageValidator:
    """Test A2A protocol specific validation."""
    
    def test_valid_agent_card(self) -> None:
        """Test validation of valid A2A agent card."""
        validator = A2AMessageValidator()
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
        
        result = validator.validate_agent_card(agent_card)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_agent_card_missing_required_fields(self) -> None:
        """Test validation fails for agent card missing required fields."""
        validator = A2AMessageValidator()
        agent_card = {
            "name": "Test Agent"
            # Missing version and capabilities
        }
        
        result = validator.validate_agent_card(agent_card)
        assert not result.is_valid
        assert any("version" in error for error in result.errors)
        assert any("capabilities" in error for error in result.errors)
    
    def test_agent_card_invalid_capabilities(self) -> None:
        """Test validation fails for invalid capabilities structure."""
        validator = A2AMessageValidator()
        agent_card = {
            "name": "Test Agent",
            "version": "1.0.0",
            "capabilities": "not_an_array"
        }
        
        result = validator.validate_agent_card(agent_card)
        assert not result.is_valid
        assert any("array" in error for error in result.errors)
    
    def test_a2a_request_validation(self) -> None:
        """Test A2A request validation includes JSON-RPC validation."""
        validator = A2AMessageValidator()
        message = {
            "jsonrpc": "2.0",
            "method": "a2a.ping",
            "id": 1
        }
        
        result = validator.validate_a2a_request(message)
        assert result.is_valid
    
    def test_a2a_method_naming_convention(self) -> None:
        """Test warning for non-A2A method naming convention."""
        validator = A2AMessageValidator()
        message = {
            "jsonrpc": "2.0",
            "method": "custom.ping",  # Doesn't follow a2a.* convention
            "id": 1
        }
        
        result = validator.validate_a2a_request(message)
        assert result.is_valid  # Should still be valid
        assert len(result.warnings) > 0
        assert any("a2a" in warning.lower() for warning in result.warnings)
    
    def test_transport_consistency_validation(self) -> None:
        """Test transport consistency validation."""
        validator = A2AMessageValidator()
        
        http_response = {"jsonrpc": "2.0", "result": {"value": 42}, "id": 1}
        grpc_response = {"jsonrpc": "2.0", "result": {"value": 42}, "id": 1}
        
        result = validator.validate_transport_consistency(http_response, grpc_response)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_transport_consistency_mismatch(self) -> None:
        """Test transport consistency validation with mismatched responses."""
        validator = A2AMessageValidator()
        
        http_response = {"jsonrpc": "2.0", "result": {"value": 42}, "id": 1}
        grpc_response = {"jsonrpc": "2.0", "result": {"value": 43}, "id": 1}  # Different result
        
        result = validator.validate_transport_consistency(http_response, grpc_response)
        assert not result.is_valid
        assert any("differs" in error for error in result.errors)