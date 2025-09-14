"""Tests for A2A Message Validator."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from any_agent.validation.a2a_message_validator import (
    A2AMessageValidator,
    A2AValidationResult,
)


class TestA2AMessageValidator:
    """Test A2A Message Validator functionality."""

    def test_init(self):
        """Test A2AMessageValidator initialization."""
        tester = A2AMessageValidator(timeout=60)
        assert tester.timeout == 60
        assert tester.validation_results == []

    def test_init_default_timeout(self):
        """Test A2AMessageValidator with default timeout."""
        tester = A2AMessageValidator()
        assert tester.timeout == 30

    @pytest.mark.asyncio
    async def test_missing_a2a_sdk(self):
        """Test behavior when A2A SDK is not available."""
        with patch(
            "any_agent.validation.a2a_message_validator.A2A_SDK_AVAILABLE", False
        ):
            tester = A2AMessageValidator()
            result = await tester.validate_agent_a2a_protocol(8080)

            assert not result["success"]
            assert "a2a-sdk not available" in result["error"]
            assert result["validations"] == []
            assert result["summary"]["total"] == 0

    @pytest.mark.asyncio
    async def test_successful_protocol_tests(self):
        """Test successful A2A protocol validation."""
        tester = A2AMessageValidator()

        # Mock the individual test methods to populate test_results
        async def mock_agent_card_discovery(base_url, httpx_client):
            tester.validation_results.append(
                A2AValidationResult(
                    scenario="agent_card_discovery",
                    success=True,
                    duration_ms=15.0,
                    details={"agent_name": "test"},
                )
            )

        async def mock_client_connection(base_url, httpx_client):
            tester.validation_results.append(
                A2AValidationResult(
                    scenario="client_connection",
                    success=True,
                    duration_ms=10.0,
                    details={"connection": "ok"},
                )
            )

        async def mock_message_exchange(base_url, httpx_client):
            tester.validation_results.append(
                A2AValidationResult(
                    scenario="basic_message_exchange",
                    success=True,
                    duration_ms=200.0,
                    details={"messages": 1},
                )
            )

        tester._validate_agent_card_discovery = mock_agent_card_discovery
        tester._validate_client_connection = mock_client_connection
        tester._validate_basic_message_exchange = mock_message_exchange

        with patch("httpx.AsyncClient"):
            result = await tester.validate_agent_a2a_protocol(8080)

        assert result["success"]
        assert result["summary"]["total"] == 3
        assert result["summary"]["passed"] == 3
        assert result["summary"]["failed"] == 0
        assert len(result["validations"]) == 3

    @pytest.mark.asyncio
    async def test_failed_protocol_tests(self):
        """Test A2A protocol validation with failures."""
        tester = A2AMessageValidator()

        # Mock individual test methods to populate test_results with failures
        async def mock_agent_card_discovery(base_url, httpx_client):
            tester.validation_results.append(
                A2AValidationResult(
                    scenario="agent_card_discovery",
                    success=False,
                    duration_ms=5.0,
                    details={},
                    error="Agent card not found",
                )
            )

        async def mock_client_connection(base_url, httpx_client):
            tester.validation_results.append(
                A2AValidationResult(
                    scenario="client_connection",
                    success=True,
                    duration_ms=10.0,
                    details={"connection": "ok"},
                )
            )

        async def mock_message_exchange(base_url, httpx_client):
            tester.validation_results.append(
                A2AValidationResult(
                    scenario="basic_message_exchange",
                    success=False,
                    duration_ms=100.0,
                    details={},
                    error="Message timeout",
                )
            )

        tester._validate_agent_card_discovery = mock_agent_card_discovery
        tester._validate_client_connection = mock_client_connection
        tester._validate_basic_message_exchange = mock_message_exchange

        with patch("httpx.AsyncClient"):
            result = await tester.validate_agent_a2a_protocol(8080)

        assert not result["success"]
        assert result["summary"]["total"] == 3
        assert result["summary"]["passed"] == 1
        assert result["summary"]["failed"] == 2
        # Note: The result format doesn't include "failed_tests" but has "validations" with all results
        failed_results = [
            validation
            for validation in result["validations"]
            if not validation["success"]
        ]
        assert len(failed_results) == 2

    @pytest.mark.asyncio
    async def test_connection_error_handling(self):
        """Test handling of connection errors."""
        tester = A2AMessageValidator()

        # Mock httpx.AsyncClient to raise connection error
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.side_effect = httpx.ConnectError("Connection failed")

            result = await tester.validate_agent_a2a_protocol(8080)

        assert not result["success"]
        assert len(tester.validation_results) > 0
        failure = tester.validation_results[0]
        assert not failure.success
        assert "Connection failed" in failure.error

    @pytest.mark.asyncio
    async def test_agent_card_discovery(self):
        """Test agent card discovery functionality."""
        tester = A2AMessageValidator()

        mock_agent_card = MagicMock()
        mock_agent_card.name = "Test Agent"
        mock_agent_card.version = "1.0.0"
        mock_agent_card.capabilities = []

        mock_resolver = MagicMock()
        mock_resolver.get_agent_card = AsyncMock(return_value=mock_agent_card)

        with patch(
            "any_agent.validation.a2a_message_validator.A2ACardResolver",
            return_value=mock_resolver,
        ):
            mock_client = MagicMock()
            await tester._validate_agent_card_discovery(
                "http://localhost:8080", mock_client
            )

        assert len(tester.validation_results) == 1
        result = tester.validation_results[0]
        assert result.scenario == "agent_card_discovery"
        assert result.success
        assert result.details["agent_name"] == "Test Agent"

    @pytest.mark.asyncio
    async def test_agent_card_discovery_missing_name(self):
        """Test agent card discovery with missing name."""
        tester = A2AMessageValidator()

        mock_agent_card = MagicMock()
        mock_agent_card.name = None  # Missing name
        mock_agent_card.version = "1.0.0"
        mock_agent_card.capabilities = []

        mock_resolver = MagicMock()
        mock_resolver.get_agent_card = AsyncMock(return_value=mock_agent_card)

        with patch(
            "any_agent.validation.a2a_message_validator.A2ACardResolver",
            return_value=mock_resolver,
        ):
            mock_client = MagicMock()
            await tester._validate_agent_card_discovery(
                "http://localhost:8080", mock_client
            )

        assert len(tester.validation_results) == 1
        result = tester.validation_results[0]
        assert result.scenario == "agent_card_discovery"
        assert not result.success
        assert "name" in result.error

    @pytest.mark.asyncio
    async def test_client_connection(self):
        """Test A2A client connection functionality."""
        tester = A2AMessageValidator()

        mock_agent_card = MagicMock()
        mock_client = MagicMock()
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_client

        mock_resolver = MagicMock()
        mock_resolver.get_agent_card = AsyncMock(return_value=mock_agent_card)

        with patch(
            "any_agent.validation.a2a_message_validator.A2ACardResolver",
            return_value=mock_resolver,
        ):
            with patch(
                "any_agent.validation.a2a_message_validator.ClientFactory",
                return_value=mock_factory,
            ):
                with patch("any_agent.validation.a2a_message_validator.ClientConfig"):
                    httpx_client = MagicMock()
                    await tester._validate_client_connection(
                        "http://localhost:8080", httpx_client
                    )

        assert len(tester.validation_results) == 1
        result = tester.validation_results[0]
        assert result.scenario == "client_connection"
        assert result.success
        assert "client_type" in result.details

    @pytest.mark.asyncio
    async def test_basic_message_exchange(self):
        """Test basic message exchange functionality."""
        tester = A2AMessageValidator()

        mock_agent_card = MagicMock()
        mock_client = MagicMock()

        # Mock async iterator for client.send_message
        async def mock_message_iterator():
            yield MagicMock(type="task", task=MagicMock())  # Task response

        mock_client.send_message = MagicMock(return_value=mock_message_iterator())

        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_client

        mock_resolver = MagicMock()
        mock_resolver.get_agent_card = AsyncMock(return_value=mock_agent_card)

        with patch(
            "any_agent.validation.a2a_message_validator.A2ACardResolver",
            return_value=mock_resolver,
        ):
            with patch(
                "any_agent.validation.a2a_message_validator.ClientFactory",
                return_value=mock_factory,
            ):
                with patch("any_agent.validation.a2a_message_validator.ClientConfig"):
                    with patch(
                        "any_agent.validation.a2a_message_validator.create_text_message_object"
                    ) as mock_create_msg:
                        mock_create_msg.return_value = "test message"
                        httpx_client = MagicMock()
                        await tester._validate_basic_message_exchange(
                            "http://localhost:8080", httpx_client
                        )

        assert len(tester.validation_results) == 1
        result = tester.validation_results[0]
        assert result.scenario == "basic_message_exchange"
        assert result.success
        assert result.details["message_sent"] == "Tell me your name"
        assert result.details["response_count"] == 1

    @pytest.mark.asyncio
    async def test_basic_message_exchange_error(self):
        """Test basic message exchange with error."""
        tester = A2AMessageValidator()

        mock_agent_card = MagicMock()
        mock_client = MagicMock()

        # Mock the client to raise an exception when send_message is called
        async def mock_message_iterator():
            raise Exception("Send failed")
            yield  # unreachable but required for generator

        mock_client.send_message = MagicMock(return_value=mock_message_iterator())

        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_client

        mock_resolver = MagicMock()
        mock_resolver.get_agent_card = AsyncMock(return_value=mock_agent_card)

        with patch(
            "any_agent.validation.a2a_message_validator.A2ACardResolver",
            return_value=mock_resolver,
        ):
            with patch(
                "any_agent.validation.a2a_message_validator.ClientFactory",
                return_value=mock_factory,
            ):
                with patch("any_agent.validation.a2a_message_validator.ClientConfig"):
                    with patch(
                        "any_agent.validation.a2a_message_validator.create_text_message_object"
                    ) as mock_create_msg:
                        mock_create_msg.return_value = "test message"
                        httpx_client = MagicMock()
                        await tester._validate_basic_message_exchange(
                            "http://localhost:8080", httpx_client
                        )

        assert len(tester.validation_results) == 1
        result = tester.validation_results[0]
        assert result.scenario == "basic_message_exchange"
        assert not result.success
        assert "Send failed" in result.error


class TestA2AValidationResult:
    """Test A2AValidationResult data class."""

    def test_a2a_validate_result_creation(self):
        """Test creating A2AValidationResult."""
        result = A2AValidationResult(
            scenario="test_scenario",
            success=True,
            duration_ms=100.5,
            details={"key": "value"},
        )

        assert result.scenario == "test_scenario"
        assert result.success is True
        assert result.duration_ms == 100.5
        assert result.details == {"key": "value"}
        assert result.error is None

    def test_a2a_validate_result_with_error(self):
        """Test creating A2AValidationResult with error."""
        result = A2AValidationResult(
            scenario="failed_test",
            success=False,
            duration_ms=50.0,
            details={},
            error="Something went wrong",
        )

        assert result.scenario == "failed_test"
        assert result.success is False
        assert result.duration_ms == 50.0
        assert result.details == {}
        assert result.error == "Something went wrong"
