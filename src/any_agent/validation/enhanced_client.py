"""Enhanced A2A Validation Client with agent card and A2A message format support."""

import json
import httpx
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from .client import A2AValidationClient, A2AValidationConfig, A2AValidationResult
from .validator import ValidationResult


@dataclass
class AgentCard:
    """Parsed A2A Agent Card."""

    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    capabilities: List[Dict[str, Any]] = field(default_factory=list)
    skills: List[Dict[str, Any]] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnhancedA2AValidationResult(A2AValidationResult):
    """Extended test result with A2A-specific information."""

    agent_card: Optional[AgentCard] = None
    agent_pattern: Optional[str] = (
        None  # 'compliance', 'conversational', 'adk', 'unknown'
    )
    a2a_compatible: Optional[bool] = None


class EnhancedA2AValidationClient(A2AValidationClient):
    """Enhanced A2A validation client with full A2A protocol support."""

    def __init__(self, config: A2AValidationConfig) -> None:
        super().__init__(config)
        self.agent_card: Optional[AgentCard] = None
        self.agent_pattern: Optional[str] = None

    async def discover_agent_card(self) -> EnhancedA2AValidationResult:
        """Discover and validate agent card at /.well-known/agent.json."""
        import time

        start_time = time.time()
        agent_card_url = f"{self.config.endpoint.rstrip('/')}/.well-known/agent.json"

        try:
            async with httpx.AsyncClient(
                timeout=self.config.timeout, verify=self.config.verify_ssl
            ) as client:
                response = await client.get(agent_card_url)
                response_time_ms = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    try:
                        card_data = response.json()
                        self.agent_card = self._parse_agent_card(card_data)

                        return EnhancedA2AValidationResult(
                            method="discover_agent_card",
                            params=None,
                            response={"agent_card": card_data},
                            validation_result=ValidationResult(
                                is_valid=True, errors=[], warnings=[]
                            ),
                            response_time_ms=response_time_ms,
                            status_code=200,
                            agent_card=self.agent_card,
                        )
                    except json.JSONDecodeError as e:
                        return EnhancedA2AValidationResult(
                            method="discover_agent_card",
                            params=None,
                            response=None,
                            validation_result=ValidationResult(
                                is_valid=False,
                                errors=[f"Invalid JSON in agent card: {e}"],
                                warnings=[],
                            ),
                            response_time_ms=response_time_ms,
                            status_code=response.status_code,
                            error="Invalid JSON in agent card",
                        )
                else:
                    return EnhancedA2AValidationResult(
                        method="discover_agent_card",
                        params=None,
                        response=None,
                        validation_result=ValidationResult(
                            is_valid=False,
                            errors=[
                                f"Agent card not found (HTTP {response.status_code})"
                            ],
                            warnings=[],
                        ),
                        response_time_ms=response_time_ms,
                        status_code=response.status_code,
                        error=f"Agent card returned {response.status_code}",
                    )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return EnhancedA2AValidationResult(
                method="discover_agent_card",
                params=None,
                response=None,
                validation_result=ValidationResult(
                    is_valid=False,
                    errors=[f"Failed to fetch agent card: {e}"],
                    warnings=[],
                ),
                response_time_ms=response_time_ms,
                error=str(e),
            )

    def _parse_agent_card(self, card_data: Dict[str, Any]) -> AgentCard:
        """Parse agent card data into structured format."""
        return AgentCard(
            name=card_data.get("name"),
            version=card_data.get("version"),
            description=card_data.get("description"),
            capabilities=card_data.get("capabilities", []),
            skills=card_data.get("skills", []),
            raw_data=card_data,
        )

    async def test_a2a_conversation(
        self, message: str, use_rest_api: bool = False
    ) -> EnhancedA2AValidationResult:
        """Test A2A conversation using proper A2A message format."""

        # A2A message format
        a2a_message = {"role": "user", "parts": [{"text": message}]}

        if use_rest_api:
            # Try REST API approach: POST /tasks/send
            return await self._test_a2a_rest_api(message, a2a_message)
        else:
            # Try JSON-RPC approach: send_message method
            return await self._test_a2a_json_rpc(message, a2a_message)

    async def _test_a2a_json_rpc(
        self, _original_message: str, a2a_message: Dict[str, Any]
    ) -> EnhancedA2AValidationResult:
        """Test A2A via JSON-RPC send_message method."""
        result = await self.call_method("send_message", {"message": a2a_message})

        # Convert to enhanced result
        enhanced_result = EnhancedA2AValidationResult(
            method=result.method,
            params=result.params,
            response=result.response,
            validation_result=result.validation_result,
            response_time_ms=result.response_time_ms,
            error=result.error,
            status_code=result.status_code,
            agent_card=self.agent_card,
            a2a_compatible=self._is_a2a_response_valid(result),
        )

        # Determine agent pattern
        if result.response and result.response.get("result"):
            enhanced_result.agent_pattern = "conversational"
        elif result.response and result.response.get("error", {}).get("code") == -32601:
            enhanced_result.agent_pattern = "compliance"
        else:
            enhanced_result.agent_pattern = "unknown"

        return enhanced_result

    async def _test_a2a_rest_api(
        self, _original_message: str, a2a_message: Dict[str, Any]
    ) -> EnhancedA2AValidationResult:
        """Test A2A via REST API /tasks/send endpoint."""
        import time
        import uuid

        start_time = time.time()

        # A2A REST API format
        task_payload = {"id": str(uuid.uuid4()), "message": a2a_message}

        tasks_url = f"{self.config.endpoint.rstrip('/')}/tasks/send"

        try:
            async with httpx.AsyncClient(
                timeout=self.config.timeout, verify=self.config.verify_ssl
            ) as client:
                response = await client.post(tasks_url, json=task_payload)
                response_time_ms = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        return EnhancedA2AValidationResult(
                            method="tasks.send",
                            params=task_payload,
                            response=response_data,
                            validation_result=ValidationResult(
                                is_valid=True, errors=[], warnings=[]
                            ),
                            response_time_ms=response_time_ms,
                            status_code=200,
                            agent_card=self.agent_card,
                            agent_pattern="conversational",
                            a2a_compatible=True,
                        )
                    except json.JSONDecodeError:
                        return EnhancedA2AValidationResult(
                            method="tasks.send",
                            params=task_payload,
                            response={"raw_text": response.text},
                            validation_result=ValidationResult(
                                is_valid=False,
                                errors=["Non-JSON response from tasks/send endpoint"],
                                warnings=[],
                            ),
                            response_time_ms=response_time_ms,
                            status_code=response.status_code,
                            error="Invalid JSON response",
                        )
                else:
                    return EnhancedA2AValidationResult(
                        method="tasks.send",
                        params=task_payload,
                        response=None,
                        validation_result=ValidationResult(
                            is_valid=False,
                            errors=[f"Tasks endpoint returned {response.status_code}"],
                            warnings=[],
                        ),
                        response_time_ms=response_time_ms,
                        status_code=response.status_code,
                        error=f"HTTP {response.status_code}",
                        agent_pattern="unknown"
                        if response.status_code == 404
                        else "error",
                    )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return EnhancedA2AValidationResult(
                method="tasks.send",
                params=task_payload,
                response=None,
                validation_result=ValidationResult(
                    is_valid=False, errors=[f"REST API call failed: {e}"], warnings=[]
                ),
                response_time_ms=response_time_ms,
                error=str(e),
            )

    def _is_a2a_response_valid(self, result: A2AValidationResult) -> bool:
        """Determine if response indicates A2A compatibility."""
        if not result.response:
            return False

        # Has a result (successful A2A call)
        if result.response.get("result"):
            return True

        # Method not found is expected for non-A2A agents
        error = result.response.get("error", {})
        if error.get("code") == -32601:
            return False

        # Other errors might still indicate A2A compatibility
        return True

    async def comprehensive_a2a_test(
        self, message: str = "Hello! What is your name?"
    ) -> Dict[str, Any]:
        """Run comprehensive A2A testing suite."""
        results: Dict[str, Any] = {}

        # 1. Discover agent card
        results["agent_card"] = await self.discover_agent_card()

        # 2. Test JSON-RPC A2A
        results["json_rpc_a2a"] = await self.test_a2a_conversation(
            message, use_rest_api=False
        )

        # 3. Test REST API A2A
        results["rest_api_a2a"] = await self.test_a2a_conversation(
            message, use_rest_api=True
        )

        # 4. Test basic protocol compliance
        results["protocol_compliance"] = await self.call_method("a2a.ping")

        # 5. Determine overall agent pattern
        agent_patterns = []
        for test_name, result in results.items():
            if hasattr(result, "agent_pattern") and result.agent_pattern:
                agent_patterns.append(result.agent_pattern)

        if "conversational" in agent_patterns:
            overall_pattern = "conversational"
        elif "compliance" in agent_patterns:
            overall_pattern = "compliance"
        else:
            overall_pattern = "unknown"

        results["summary"] = {
            "agent_pattern": overall_pattern,
            "agent_card_available": results["agent_card"].validation_result.is_valid,
            "a2a_json_rpc_support": results["json_rpc_a2a"].agent_pattern
            == "conversational",
            "a2a_rest_api_support": results["rest_api_a2a"].agent_pattern
            == "conversational",
            "protocol_compliant": results[
                "protocol_compliance"
            ].validation_result.is_valid,
        }

        return results
