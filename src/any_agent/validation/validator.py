"""JSON-RPC 2.0 and A2A Protocol Message Validators."""

import json
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

try:
    from jsonschema import validate, ValidationError

    JSONSCHEMA_AVAILABLE = True
except ImportError:
    validate = None  # type: ignore
    ValidationError = None  # type: ignore
    JSONSCHEMA_AVAILABLE = False


@dataclass
class ValidationResult:
    """Result of message validation."""

    is_valid: bool
    errors: List[str]
    warnings: List[str]


class JSONRPCValidator:
    """Validates JSON-RPC 2.0 message format compliance."""

    # JSON-RPC 2.0 Request Schema
    REQUEST_SCHEMA = {
        "type": "object",
        "properties": {
            "jsonrpc": {"type": "string", "enum": ["2.0"]},
            "method": {"type": "string"},
            "params": {"oneOf": [{"type": "array"}, {"type": "object"}]},
            "id": {"oneOf": [{"type": "string"}, {"type": "number"}, {"type": "null"}]},
        },
        "required": ["jsonrpc", "method"],
        "additionalProperties": False,
    }

    # JSON-RPC 2.0 Response Schema
    RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "jsonrpc": {"type": "string", "enum": ["2.0"]},
            "result": {},
            "error": {
                "type": "object",
                "properties": {
                    "code": {"type": "integer"},
                    "message": {"type": "string"},
                    "data": {},
                },
                "required": ["code", "message"],
                "additionalProperties": False,
            },
            "id": {"oneOf": [{"type": "string"}, {"type": "number"}, {"type": "null"}]},
        },
        "required": ["jsonrpc", "id"],
        "oneOf": [{"required": ["result"]}, {"required": ["error"]}],
        "not": {"allOf": [{"required": ["result"]}, {"required": ["error"]}]},
        "additionalProperties": False,
    }

    # JSON-RPC 2.0 Notification Schema
    NOTIFICATION_SCHEMA = {
        "type": "object",
        "properties": {
            "jsonrpc": {"type": "string", "enum": ["2.0"]},
            "method": {"type": "string"},
            "params": {"oneOf": [{"type": "array"}, {"type": "object"}]},
        },
        "required": ["jsonrpc", "method"],
        "additionalProperties": False,
    }

    def validate_request(self, message: Dict[str, Any]) -> ValidationResult:
        """Validate JSON-RPC 2.0 request message."""
        errors: List[str] = []
        warnings: List[str] = []

        if not JSONSCHEMA_AVAILABLE:
            errors.append(
                "jsonschema not available - install with: pip install jsonschema"
            )
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        try:
            validate(instance=message, schema=self.REQUEST_SCHEMA)
        except ValidationError as e:
            errors.append(f"JSON-RPC request validation error: {e.message}")

        # Additional validation rules
        if "id" not in message:
            warnings.append("Request without 'id' field is treated as notification")

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def validate_response(self, message: Dict[str, Any]) -> ValidationResult:
        """Validate JSON-RPC 2.0 response message."""
        errors: List[str] = []
        warnings: List[str] = []

        if not JSONSCHEMA_AVAILABLE:
            errors.append(
                "jsonschema not available - install with: pip install jsonschema"
            )
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        try:
            validate(instance=message, schema=self.RESPONSE_SCHEMA)
        except ValidationError as e:
            errors.append(f"JSON-RPC response validation error: {e.message}")

        # Check for both result and error (not allowed)
        if "result" in message and "error" in message:
            errors.append("Response cannot contain both 'result' and 'error' fields")

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def validate_notification(self, message: Dict[str, Any]) -> ValidationResult:
        """Validate JSON-RPC 2.0 notification message."""
        errors: List[str] = []
        warnings: List[str] = []

        if not JSONSCHEMA_AVAILABLE:
            errors.append(
                "jsonschema not available - install with: pip install jsonschema"
            )
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        try:
            validate(instance=message, schema=self.NOTIFICATION_SCHEMA)
        except ValidationError as e:
            errors.append(f"JSON-RPC notification validation error: {e.message}")

        # Check that notification has no id
        if "id" in message:
            errors.append("Notification must not include 'id' field")

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def validate_message(self, message: Union[str, Dict[str, Any]]) -> ValidationResult:
        """Validate any JSON-RPC 2.0 message (auto-detect type)."""
        errors: List[str] = []
        warnings: List[str] = []

        if not JSONSCHEMA_AVAILABLE:
            errors.append(
                "jsonschema not available - install with: pip install jsonschema"
            )
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        # Parse JSON if string
        if isinstance(message, str):
            try:
                message = json.loads(message)
            except json.JSONDecodeError as e:
                return ValidationResult(
                    is_valid=False, errors=[f"Invalid JSON format: {e}"], warnings=[]
                )

        # Check basic JSON-RPC structure
        if not isinstance(message, dict):
            return ValidationResult(
                is_valid=False, errors=["Message must be a JSON object"], warnings=[]
            )

        if message.get("jsonrpc") != "2.0":
            errors.append("JSON-RPC version must be exactly '2.0'")

        # Determine message type and validate accordingly
        if "method" in message:
            if "id" in message:
                # Request
                result = self.validate_request(message)
            else:
                # Notification
                result = self.validate_notification(message)
        else:
            # Response
            result = self.validate_response(message)

        return ValidationResult(
            is_valid=result.is_valid and len(errors) == 0,
            errors=errors + result.errors,
            warnings=warnings + result.warnings,
        )


class A2AMessageValidator:
    """Validates A2A Protocol specific message requirements."""

    def __init__(self) -> None:
        self.jsonrpc_validator = JSONRPCValidator()

    def validate_agent_card(self, agent_card: Dict[str, Any]) -> ValidationResult:
        """Validate A2A Agent Card structure."""
        errors: List[str] = []
        warnings: List[str] = []

        required_fields = ["name", "version", "capabilities"]
        for field in required_fields:
            if field not in agent_card:
                errors.append(f"Agent card missing required field: {field}")

        # Validate capabilities structure
        if "capabilities" in agent_card:
            capabilities = agent_card["capabilities"]
            if not isinstance(capabilities, list):
                errors.append("Agent card 'capabilities' must be an array")
            else:
                for i, capability in enumerate(capabilities):
                    if not isinstance(capability, dict):
                        errors.append(f"Capability {i} must be an object")
                    elif "method" not in capability:
                        errors.append(f"Capability {i} missing 'method' field")

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def validate_a2a_request(self, message: Dict[str, Any]) -> ValidationResult:
        """Validate A2A protocol request message."""
        # First validate JSON-RPC compliance
        jsonrpc_result = self.jsonrpc_validator.validate_message(message)

        errors = list(jsonrpc_result.errors)
        warnings = list(jsonrpc_result.warnings)

        # A2A specific validations
        if "method" in message:
            method = message["method"]
            # Check for A2A method naming conventions
            if not method.startswith("a2a."):
                warnings.append(
                    f"Method '{method}' does not follow A2A naming convention (a2a.*)"
                )

        return ValidationResult(
            is_valid=jsonrpc_result.is_valid
            and len(errors) == jsonrpc_result.errors.__len__(),
            errors=errors,
            warnings=warnings,
        )

    def validate_transport_consistency(
        self,
        http_response: Dict[str, Any],
        grpc_response: Optional[Dict[str, Any]] = None,
        websocket_response: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """Validate functional equivalence across A2A transport protocols."""
        errors: List[str] = []
        warnings: List[str] = []

        responses = [
            r
            for r in [http_response, grpc_response, websocket_response]
            if r is not None
        ]

        if len(responses) < 2:
            warnings.append(
                "Cannot validate transport consistency with fewer than 2 responses"
            )
            return ValidationResult(is_valid=True, errors=errors, warnings=warnings)

        # Compare result values for semantic equivalence
        base_result = responses[0].get("result")
        for i, response in enumerate(responses[1:], 1):
            if response.get("result") != base_result:
                errors.append(
                    f"Transport response {i} result differs from base response"
                )

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )
