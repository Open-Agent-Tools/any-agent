"""A2A Validation Client with HTTP abstraction using httpx."""

import json
import asyncio
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
import httpx

from .validator import JSONRPCValidator, A2AMessageValidator, ValidationResult


@dataclass
class A2AValidationConfig:
    """Configuration for A2A validation client."""

    endpoint: str
    timeout: float = 30.0
    max_retries: int = 3
    auth_token: Optional[str] = None
    auth_type: str = "bearer"  # bearer, api_key
    verify_ssl: bool = True
    headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class A2AValidationResult:
    """Result of an A2A validation method call."""

    method: str
    params: Optional[Union[Dict[str, Any], List[Any]]]
    response: Optional[Dict[str, Any]]
    validation_result: ValidationResult
    response_time_ms: float
    error: Optional[str] = None
    status_code: Optional[int] = None


class A2AValidationClient:
    """HTTP client for testing A2A protocol compliance."""

    def __init__(self, config: A2AValidationConfig) -> None:
        self.config = config
        self.jsonrpc_validator = JSONRPCValidator()
        self.a2a_validator = A2AMessageValidator()
        self._request_id = 0

        # Setup HTTP client
        headers = {"Content-Type": "application/json", **self.config.headers}

        if self.config.auth_token:
            if self.config.auth_type == "bearer":
                headers["Authorization"] = f"Bearer {self.config.auth_token}"
            elif self.config.auth_type == "api_key":
                headers["X-API-Key"] = self.config.auth_token

        self.client = httpx.AsyncClient(
            timeout=self.config.timeout, verify=self.config.verify_ssl, headers=headers
        )

    async def __aenter__(self) -> "A2AValidationClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, _exc_type: Any, _exc_val: Any, _exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.client.aclose()

    def _get_next_id(self) -> int:
        """Get next request ID."""
        self._request_id += 1
        return self._request_id

    def _build_request(
        self,
        method: str,
        params: Optional[Union[Dict[str, Any], List[Any]]] = None,
        request_id: Optional[Union[str, int]] = None,
    ) -> Dict[str, Any]:
        """Build JSON-RPC 2.0 request message."""
        request: Dict[str, Any] = {"jsonrpc": "2.0", "method": method}

        if params is not None:
            request["params"] = params

        if request_id is not None:
            request["id"] = request_id
        else:
            request["id"] = self._get_next_id()

        return request

    async def call_method(
        self,
        method: str,
        params: Optional[Union[Dict[str, Any], List[Any]]] = None,
        validate_request: bool = True,
        validate_response: bool = True,
    ) -> A2AValidationResult:
        """Call A2A method and return test result."""
        import time

        # Build request
        request = self._build_request(method, params)

        # Validate request if requested
        request_validation = None
        if validate_request:
            request_validation = self.a2a_validator.validate_a2a_request(request)
            if not request_validation.is_valid:
                return A2AValidationResult(
                    method=method,
                    params=params,
                    response=None,
                    validation_result=request_validation,
                    response_time_ms=0,
                    error="Request validation failed",
                )

        # Make HTTP request
        start_time = time.time()
        try:
            response = await self.client.post(self.config.endpoint, json=request)
            response_time_ms = (time.time() - start_time) * 1000

            # Parse response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                return A2AValidationResult(
                    method=method,
                    params=params,
                    response=None,
                    validation_result=ValidationResult(
                        is_valid=False,
                        errors=["Response is not valid JSON"],
                        warnings=[],
                    ),
                    response_time_ms=response_time_ms,
                    error="Invalid JSON response",
                    status_code=response.status_code,
                )

            # Validate response if requested
            response_validation = ValidationResult(
                is_valid=True, errors=[], warnings=[]
            )
            if validate_response:
                response_validation = self.jsonrpc_validator.validate_response(
                    response_data
                )

            return A2AValidationResult(
                method=method,
                params=params,
                response=response_data,
                validation_result=response_validation,
                response_time_ms=response_time_ms,
                status_code=response.status_code,
            )

        except httpx.RequestError as e:
            response_time_ms = (time.time() - start_time) * 1000
            return A2AValidationResult(
                method=method,
                params=params,
                response=None,
                validation_result=ValidationResult(
                    is_valid=False, errors=[f"HTTP request failed: {e}"], warnings=[]
                ),
                response_time_ms=response_time_ms,
                error=str(e),
            )

    async def send_notification(
        self, method: str, params: Optional[Union[Dict[str, Any], List[Any]]] = None
    ) -> A2AValidationResult:
        """Send JSON-RPC notification (no response expected)."""
        import time

        # Build notification (no id field)
        request: Dict[str, Any] = {"jsonrpc": "2.0", "method": method}

        if params is not None:
            request["params"] = params

        # Validate notification
        validation_result = self.jsonrpc_validator.validate_notification(request)
        if not validation_result.is_valid:
            return A2AValidationResult(
                method=method,
                params=params,
                response=None,
                validation_result=validation_result,
                response_time_ms=0,
                error="Notification validation failed",
            )

        # Send notification
        start_time = time.time()
        try:
            response = await self.client.post(self.config.endpoint, json=request)
            response_time_ms = (time.time() - start_time) * 1000

            return A2AValidationResult(
                method=method,
                params=params,
                response=None,  # Notifications don't expect responses
                validation_result=ValidationResult(
                    is_valid=True, errors=[], warnings=[]
                ),
                response_time_ms=response_time_ms,
                status_code=response.status_code,
            )

        except httpx.RequestError as e:
            response_time_ms = (time.time() - start_time) * 1000
            return A2AValidationResult(
                method=method,
                params=params,
                response=None,
                validation_result=ValidationResult(
                    is_valid=False, errors=[f"HTTP request failed: {e}"], warnings=[]
                ),
                response_time_ms=response_time_ms,
                error=str(e),
            )

    async def discover_methods(self) -> A2AValidationResult:
        """Attempt to discover available A2A methods."""
        # Try common A2A discovery methods
        discovery_methods = [
            "a2a.listMethods",
            "a2a.discover",
            "a2a.capabilities",
            "system.listMethods",
            "rpc.discover",
        ]

        for method in discovery_methods:
            result = await self.call_method(method)
            if result.response and not result.error:
                return result

        # If no discovery method works, return failure
        return A2AValidationResult(
            method="discovery",
            params=None,
            response=None,
            validation_result=ValidationResult(
                is_valid=False,
                errors=["No method discovery endpoint found"],
                warnings=[],
            ),
            response_time_ms=0,
            error="Method discovery failed",
        )

    async def get_agent_card(self) -> A2AValidationResult:
        """Retrieve and validate A2A Agent Card."""
        # Try to get agent card
        result = await self.call_method("a2a.getAgentCard")

        if result.response and "result" in result.response:
            # Validate agent card structure
            agent_card = result.response["result"]
            card_validation = self.a2a_validator.validate_agent_card(agent_card)

            return A2AValidationResult(
                method="a2a.getAgentCard",
                params=None,
                response=result.response,
                validation_result=card_validation,
                response_time_ms=result.response_time_ms,
                status_code=result.status_code,
            )

        return result

    async def validate_endpoint_health(self) -> A2AValidationResult:
        """Check if A2A endpoint is healthy and responding."""
        # Try a simple ping or health check
        health_methods = ["a2a.ping", "a2a.health", "system.ping", "ping"]

        for method in health_methods:
            result = await self.call_method(method)
            if result.status_code == 200:
                return result

        # If no health method works, try basic method discovery
        return await self.discover_methods()

    async def batch_call(
        self, methods: List[Dict[str, Any]]
    ) -> List[A2AValidationResult]:
        """Execute multiple A2A method calls in parallel."""
        tasks = []
        for method_call in methods:
            method = method_call["method"]
            params = method_call.get("params")
            task = self.call_method(method, params)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results
        final_results: List[A2AValidationResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(
                    A2AValidationResult(
                        method=methods[i]["method"],
                        params=methods[i].get("params"),
                        response=None,
                        validation_result=ValidationResult(
                            is_valid=False,
                            errors=[f"Exception during method call: {result}"],
                            warnings=[],
                        ),
                        response_time_ms=0,
                        error=str(result),
                    )
                )
            else:
                # result is guaranteed to be A2AValidationResult here
                assert isinstance(result, A2AValidationResult)
                final_results.append(result)

        return final_results
