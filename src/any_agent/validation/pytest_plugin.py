"""Pytest plugin for A2A protocol testing integration."""

import pytest
from typing import Dict, Any, List
from pathlib import Path
import yaml

from .client import A2AValidationConfig, A2AValidationClient
from .engine import (
    ValidationDiscoveryEngine,
    ValidationExecutionEngine,
    TestSuiteResult,
)


def pytest_addoption(parser: Any) -> None:
    """Add A2A-specific command line options to pytest."""
    group = parser.getgroup("a2a", "A2A Protocol Testing")

    group.addoption(
        "--a2a-endpoint",
        action="store",
        default="http://localhost:8080",
        help="A2A agent endpoint URL (default: http://localhost:8080)",
    )

    group.addoption(
        "--a2a-config", action="store", help="Path to A2A test configuration file"
    )

    group.addoption(
        "--a2a-auth-token", action="store", help="Authentication token for A2A requests"
    )

    group.addoption(
        "--a2a-auth-type",
        action="store",
        default="bearer",
        choices=["bearer", "api_key"],
        help="Authentication type (default: bearer)",
    )

    group.addoption(
        "--a2a-timeout",
        action="store",
        type=float,
        default=30.0,
        help="Request timeout in seconds (default: 30.0)",
    )

    group.addoption(
        "--a2a-verify-ssl",
        action="store_true",
        default=True,
        help="Verify SSL certificates (default: True)",
    )

    group.addoption(
        "--a2a-report-format",
        action="store",
        default="text",
        choices=["text", "json", "junit"],
        help="Test report format (default: text)",
    )

    group.addoption(
        "--a2a-generate-tests",
        action="store_true",
        help="Auto-generate A2A compliance tests",
    )


def pytest_configure(config: Any) -> None:
    """Configure pytest for A2A testing."""
    # Register custom markers
    config.addinivalue_line("markers", "a2a: mark test as A2A protocol test")
    config.addinivalue_line(
        "markers", "a2a_compliance: mark test as A2A protocol compliance test"
    )
    config.addinivalue_line(
        "markers", "a2a_performance: mark test as A2A performance test"
    )
    config.addinivalue_line(
        "markers", "a2a_error_handling: mark test as A2A error handling test"
    )


@pytest.fixture(scope="session")
def a2a_config(request: Any) -> A2AValidationConfig:
    """Create A2A test configuration from command line options and config file."""
    # Start with command line options
    config_data = {
        "endpoint": request.config.getoption("--a2a-endpoint"),
        "timeout": request.config.getoption("--a2a-timeout"),
        "auth_token": request.config.getoption("--a2a-auth-token"),
        "auth_type": request.config.getoption("--a2a-auth-type"),
        "verify_ssl": request.config.getoption("--a2a-verify-ssl"),
    }

    # Load config file if provided
    config_file = request.config.getoption("--a2a-config")
    if config_file:
        config_path = Path(config_file)
        if config_path.exists():
            with open(config_path, "r") as f:
                if config_path.suffix.lower() in [".yaml", ".yml"]:
                    file_config = yaml.safe_load(f)
                else:
                    import json

                    file_config = json.load(f)

            # Merge file config with command line options (CLI takes precedence)
            for key, value in file_config.items():
                if key not in config_data or config_data[key] is None:
                    config_data[key] = value

    # Remove None values
    config_data = {k: v for k, v in config_data.items() if v is not None}

    return A2AValidationConfig(**config_data)


@pytest.fixture(scope="session")
async def a2a_client(a2a_config: A2AValidationConfig) -> A2AValidationClient:  # type: ignore[misc]
    """Create A2A test client session fixture."""
    async with A2AValidationClient(a2a_config) as client:
        # Validate endpoint health before running tests
        health_result = await client.validate_endpoint_health()
        if health_result.error:
            pytest.skip(f"A2A endpoint not healthy: {health_result.error}")

        yield client


@pytest.fixture
def a2a_discovery_engine(a2a_client: A2AValidationClient) -> ValidationDiscoveryEngine:
    """Create test discovery engine."""
    return ValidationDiscoveryEngine(a2a_client)


@pytest.fixture
def a2a_execution_engine(a2a_client: A2AValidationClient) -> ValidationExecutionEngine:
    """Create test execution engine."""
    return ValidationExecutionEngine(a2a_client)


class A2ATestCollector:
    """Collects and generates A2A tests dynamically."""

    def __init__(self, discovery_engine: ValidationDiscoveryEngine) -> None:
        self.discovery_engine = discovery_engine

    async def collect_compliance_tests(self) -> List[Dict[str, Any]]:
        """Collect A2A protocol compliance tests."""
        test_suite = await self.discovery_engine.generate_test_suite(
            "Dynamic A2A Compliance Tests"
        )

        return [
            {
                "name": test_case.name,
                "description": test_case.description,
                "method": test_case.method,
                "params": test_case.params,
                "category": test_case.category.value,
                "severity": test_case.severity.value,
                "should_fail": test_case.should_fail,
                "timeout_ms": test_case.timeout_ms,
                "metadata": test_case.metadata,
            }
            for test_case in test_suite.test_cases
        ]


def pytest_generate_tests(metafunc: Any) -> None:
    """Generate A2A tests dynamically if requested."""
    if metafunc.config.getoption("--a2a-generate-tests"):
        if "a2a_test_case" in metafunc.fixturenames:
            # This would need to be implemented with proper async handling
            # For now, we'll use a simpler approach
            metafunc.parametrize(
                "a2a_test_case",
                [
                    {
                        "name": "basic_ping_test",
                        "method": "a2a.ping",
                        "params": None,
                        "should_fail": False,
                    },
                    {
                        "name": "method_not_found_test",
                        "method": "nonexistent.method",
                        "params": None,
                        "should_fail": True,
                    },
                ],
            )


def pytest_collection_modifyitems(config: Any, items: List[Any]) -> None:
    """Modify collected test items for A2A testing."""
    if not config.getoption("--a2a-generate-tests"):
        return

    # Add A2A marker to generated tests
    for item in items:
        if "a2a_test_case" in item.fixturenames:
            item.add_marker(pytest.mark.a2a)


class A2ATestReporter:
    """Custom test reporter for A2A test results."""

    def __init__(self) -> None:
        self.results: List[TestSuiteResult] = []

    def add_result(self, result: TestSuiteResult) -> None:
        """Add test suite result."""
        self.results.append(result)

    def generate_report(self, format_type: str = "text") -> str:
        """Generate consolidated report."""
        if not self.results:
            return "No A2A test results available."

        # For now, just use the first result's reporting
        # In a full implementation, this would consolidate multiple results
        from .engine import ValidationExecutionEngine

        engine = ValidationExecutionEngine(None)  # type: ignore[arg-type]  # We only need the reporting methods
        return engine.generate_report(self.results[0], format_type)


# Global reporter instance
_a2a_reporter = A2ATestReporter()


@pytest.fixture
def a2a_reporter() -> A2ATestReporter:
    """Get the global A2A test reporter."""
    return _a2a_reporter


def pytest_terminal_summary(
    terminalreporter: Any, _exitstatus: int, config: Any
) -> None:
    """Add A2A test summary to pytest output."""
    if not _a2a_reporter.results:
        return

    report_format = config.getoption("--a2a-report-format")
    report = _a2a_reporter.generate_report(report_format)

    terminalreporter.section("A2A Protocol Test Results")
    terminalreporter.line(report)


# Test function templates for generated tests
@pytest.mark.a2a
async def test_a2a_method_call(
    a2a_client: A2AValidationClient, a2a_test_case: Dict[str, Any]
) -> None:
    """Template for dynamically generated A2A method tests."""
    result = await a2a_client.call_method(
        a2a_test_case["method"], a2a_test_case.get("params")
    )

    if a2a_test_case.get("should_fail", False):
        assert result.error is not None or not result.validation_result.is_valid
    else:
        assert result.error is None
        assert result.validation_result.is_valid
        assert result.response is not None


@pytest.mark.a2a_compliance
async def test_a2a_protocol_compliance(
    a2a_client: A2AValidationClient,
    a2a_discovery_engine: ValidationDiscoveryEngine,
    a2a_execution_engine: ValidationExecutionEngine,
    a2a_reporter: A2ATestReporter,
) -> None:
    """Test A2A protocol compliance comprehensively."""
    # Generate and execute compliance test suite
    test_suite = await a2a_discovery_engine.generate_test_suite()
    result = await a2a_execution_engine.execute_test_suite(test_suite)

    # Add to reporter
    a2a_reporter.add_result(result)

    # Assert overall success
    assert result.failed_tests == 0, (
        f"A2A compliance failed: {result.failed_tests} out of {result.total_tests} tests failed"
    )


@pytest.mark.a2a_performance
async def test_a2a_response_time(a2a_client: A2AValidationClient) -> None:
    """Test A2A response time performance."""
    result = await a2a_client.call_method("a2a.ping")

    # Assert response time is reasonable (configurable threshold)
    assert result.response_time_ms < 5000, (
        f"Response time {result.response_time_ms}ms exceeds 5000ms threshold"
    )
    assert result.validation_result.is_valid


@pytest.mark.a2a_error_handling
async def test_a2a_error_handling(a2a_client: A2AValidationClient) -> None:
    """Test A2A error handling for invalid requests."""
    # Test method not found
    result = await a2a_client.call_method("nonexistent.method")

    # Should get a proper JSON-RPC error response
    assert result.response is not None
    assert "error" in result.response
    assert result.response["error"]["code"] == -32601  # Method not found
