"""A2A Protocol Message Validation for deployed agents.

This module provides comprehensive A2A protocol validation capabilities
based on the validated client implementation patterns.
"""

import logging
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

import httpx

from ..shared.url_utils import localhost_urls

try:
    from a2a.client import ClientFactory, A2ACardResolver, ClientConfig
    from a2a.client.helpers import create_text_message_object

    A2A_SDK_AVAILABLE = True
except ImportError:
    A2A_SDK_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class A2AValidationResult:
    """Result of an A2A validation scenario."""

    scenario: str
    success: bool
    duration_ms: float
    details: Dict[str, Any]
    error: Optional[str] = None


class A2AMessageValidator:
    """A2A protocol message validation for deployed agents."""

    def __init__(self, timeout: int = 30):
        """Initialize A2A message validator.

        Args:
            timeout: Timeout in seconds for A2A operations
        """
        self.timeout = timeout
        self.validation_results: List[A2AValidationResult] = []

        # Suppress verbose logging from A2A SDK components to avoid data dumps
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("a2a.client.card_resolver").setLevel(logging.WARNING)
        logging.getLogger("a2a.client").setLevel(logging.WARNING)

    async def validate_agent_a2a_protocol(self, port: int) -> Dict[str, Any]:
        """Run comprehensive A2A protocol validation against deployed agent.

        Args:
            port: Port where the A2A agent is running

        Returns:
            Dictionary with comprehensive validation results
        """
        if not A2A_SDK_AVAILABLE:
            return {
                "success": False,
                "error": "a2a-sdk not available - install with: pip install a2a-sdk>=0.1.0",
                "validations": [],
                "summary": {"total": 0, "passed": 0, "failed": 0, "duration_ms": 0},
            }

        logger.info(f"Starting A2A protocol validation on port {port}")
        self.validation_results = []
        start_time = time.time()

        base_url = localhost_urls.base_url(port)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as httpx_client:
                # Run core test scenarios
                await self._validate_agent_card_discovery(base_url, httpx_client)
                await self._validate_client_connection(base_url, httpx_client)
                await self._validate_basic_message_exchange(base_url, httpx_client)

        except Exception as e:
            logger.error(f"A2A protocol validation failed: {e}")
            self.validation_results.append(
                A2AValidationResult(
                    scenario="overall_connection",
                    success=False,
                    duration_ms=0,
                    details={},
                    error=f"Failed to connect to A2A server: {e}",
                )
            )

        total_duration = (time.time() - start_time) * 1000

        # Generate summary
        passed_validations = [r for r in self.validation_results if r.success]
        failed_validations = [r for r in self.validation_results if not r.success]

        return {
            "success": len(failed_validations) == 0,
            "validations": [
                self._validation_result_to_dict(r) for r in self.validation_results
            ],
            "summary": {
                "total": len(self.validation_results),
                "passed": len(passed_validations),
                "failed": len(failed_validations),
                "duration_ms": total_duration,
            },
        }

    async def _validate_agent_card_discovery(
        self, base_url: str, httpx_client: httpx.AsyncClient
    ) -> None:
        """Validate agent card resolution and structure."""
        scenario = "agent_card_discovery"
        start_time = time.time()

        try:
            logger.info("Validating agent card discovery...")
            resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
            agent_card = await resolver.get_agent_card()
            duration_ms = (time.time() - start_time) * 1000

            # Validate agent card structure
            details = {
                "agent_name": getattr(agent_card, "name", None),
                "version": getattr(agent_card, "version", None),
                "capabilities": getattr(agent_card, "capabilities", None),
                "card_type": type(agent_card).__name__,
            }

            # Validation checks
            success = True
            validation_errors = []

            if not hasattr(agent_card, "name") or not agent_card.name:
                validation_errors.append("Agent card missing 'name' field")
                success = False

            if not hasattr(agent_card, "capabilities"):
                validation_errors.append("Agent card missing 'capabilities' field")
                success = False

            details["validation_errors"] = validation_errors

            self.validation_results.append(
                A2AValidationResult(
                    scenario=scenario,
                    success=success,
                    duration_ms=duration_ms,
                    details=details,
                    error=None
                    if success
                    else f"Validation failed: {validation_errors}",
                )
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Agent card discovery failed: {e}")
            self.validation_results.append(
                A2AValidationResult(
                    scenario=scenario,
                    success=False,
                    duration_ms=duration_ms,
                    details={"error_type": type(e).__name__},
                    error=str(e),
                )
            )

    async def _validate_client_connection(
        self, base_url: str, httpx_client: httpx.AsyncClient
    ) -> None:
        """Validate A2A client connection and initialization."""
        scenario = "client_connection"
        start_time = time.time()

        try:
            logger.info("Validating A2A client connection...")

            # Get agent card first
            resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
            agent_card = await resolver.get_agent_card()

            # Test ClientFactory pattern
            client_config = ClientConfig(httpx_client=httpx_client)
            factory = ClientFactory(config=client_config)
            client = factory.create(card=agent_card)

            duration_ms = (time.time() - start_time) * 1000

            details = {
                "client_type": type(client).__name__,
                "factory_type": type(factory).__name__,
                "config_type": type(client_config).__name__,
                "initialization": "success",
            }

            self.validation_results.append(
                A2AValidationResult(
                    scenario=scenario,
                    success=True,
                    duration_ms=duration_ms,
                    details=details,
                )
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Client connection failed: {e}")
            self.validation_results.append(
                A2AValidationResult(
                    scenario=scenario,
                    success=False,
                    duration_ms=duration_ms,
                    details={"error_type": type(e).__name__},
                    error=str(e),
                )
            )

    async def _validate_basic_message_exchange(
        self, base_url: str, httpx_client: httpx.AsyncClient
    ) -> None:
        """Validate basic message sending and response structure."""
        scenario = "basic_message_exchange"
        start_time = time.time()

        try:
            logger.info("Validating basic message exchange...")

            # Setup client
            resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
            agent_card = await resolver.get_agent_card()

            client_config = ClientConfig(httpx_client=httpx_client)
            factory = ClientFactory(config=client_config)
            client = factory.create(card=agent_card)

            # Send validation message
            validation_message = "Tell me your name"
            message = create_text_message_object(content=validation_message)

            responses = []
            response_count = 0
            async for response in client.send_message(message):
                responses.append(response)
                response_count += 1
                # Limit responses to prevent hanging on streaming
                if response_count >= 10:
                    break

            duration_ms = (time.time() - start_time) * 1000

            # Analyze responses
            task_responses = []
            message_responses = []
            other_responses = []

            for response in responses:
                if isinstance(response, tuple) and len(response) >= 1:
                    # Task tuple format
                    task_obj = response[0]
                    task_responses.append(
                        {
                            "type": "task_tuple",
                            "task_type": type(task_obj).__name__,
                            "has_artifacts": hasattr(task_obj, "artifacts"),
                            "has_status": hasattr(task_obj, "status"),
                            "has_context_id": hasattr(task_obj, "context_id"),
                        }
                    )
                elif hasattr(response, "__class__") and "Message" in str(
                    response.__class__
                ):
                    message_responses.append(
                        {"type": "message", "message_type": type(response).__name__}
                    )
                else:
                    other_responses.append(
                        {"type": "other", "response_type": type(response).__name__}
                    )

            details = {
                "message_sent": validation_message,
                "response_count": len(responses),
                "task_responses": task_responses,
                "message_responses": message_responses,
                "other_responses": other_responses,
                "total_response_types": {
                    "tasks": len(task_responses),
                    "messages": len(message_responses),
                    "other": len(other_responses),
                },
            }

            # Success if we got at least one response
            success = len(responses) > 0

            self.validation_results.append(
                A2AValidationResult(
                    scenario=scenario,
                    success=success,
                    duration_ms=duration_ms,
                    details=details,
                    error=None if success else "No responses received",
                )
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Message exchange failed: {e}")
            self.validation_results.append(
                A2AValidationResult(
                    scenario=scenario,
                    success=False,
                    duration_ms=duration_ms,
                    details={"error_type": type(e).__name__},
                    error=str(e),
                )
            )

    def _validation_result_to_dict(self, result: A2AValidationResult) -> Dict[str, Any]:
        """Convert validation result to dictionary format."""
        return {
            "scenario": result.scenario,
            "success": result.success,
            "duration_ms": result.duration_ms,
            "details": result.details,
            "error": result.error,
        }

    @staticmethod
    def is_a2a_validation_available() -> bool:
        """Check if A2A validation is available (a2a-sdk installed)."""
        return A2A_SDK_AVAILABLE
