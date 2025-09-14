"""Validation Discovery and Execution Engine for A2A Protocol Validation."""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json

from .client import A2AValidationClient, A2AValidationResult


class ValidationSeverity(Enum):
    """Validation severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ValidationCategory(Enum):
    """Validation categories."""

    PROTOCOL_COMPLIANCE = "protocol_compliance"
    METHOD_DISCOVERY = "method_discovery"
    ERROR_HANDLING = "error_handling"
    PERFORMANCE = "performance"
    SECURITY = "security"
    INTEROPERABILITY = "interoperability"


@dataclass
class TestCase:
    """Individual test case definition."""

    name: str
    description: str
    method: str
    params: Any  # Can be invalid types for error testing
    category: ValidationCategory
    severity: ValidationSeverity
    expected_result: Optional[Any] = None
    should_fail: bool = False
    timeout_ms: float = 5000
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestSuite:
    """Collection of test cases."""

    name: str
    description: str
    test_cases: List[TestCase]
    setup: Optional[Callable] = None
    teardown: Optional[Callable] = None


@dataclass
class TestExecutionResult:
    """Result of executing a test suite."""

    test_case: TestCase
    a2a_result: Optional[A2AValidationResult]
    passed: bool
    execution_time_ms: float
    error_message: Optional[str] = None


@dataclass
class TestSuiteResult:
    """Results from executing an entire test suite."""

    test_suite: TestSuite
    results: List[TestExecutionResult]
    total_tests: int
    passed_tests: int
    failed_tests: int
    execution_time_ms: float
    summary: Dict[str, Any] = field(default_factory=dict)


class ValidationDiscoveryEngine:
    """Discovers and generates A2A validation cases."""

    def __init__(self, client: A2AValidationClient) -> None:
        self.client = client

    async def discover_agent_capabilities(self) -> List[str]:
        """Discover available methods from agent."""
        methods = []

        # Try to get agent card first
        agent_card_result = await self.client.get_agent_card()
        if agent_card_result.response and "result" in agent_card_result.response:
            agent_card = agent_card_result.response["result"]
            if "capabilities" in agent_card:
                for capability in agent_card["capabilities"]:
                    if "method" in capability:
                        methods.append(capability["method"])

        # Try method discovery
        discovery_result = await self.client.discover_methods()
        if discovery_result.response and "result" in discovery_result.response:
            discovered_methods = discovery_result.response["result"]
            if isinstance(discovered_methods, list):
                methods.extend(discovered_methods)

        return list(set(methods))  # Remove duplicates

    def generate_protocol_compliance_tests(self, methods: List[str]) -> List[TestCase]:
        """Generate JSON-RPC 2.0 protocol compliance tests."""
        test_cases = []

        # Basic protocol compliance tests
        test_cases.extend(
            [
                TestCase(
                    name="json_rpc_version_validation",
                    description="Validate JSON-RPC version requirement",
                    method="a2a.ping",
                    params=None,
                    category=ValidationCategory.PROTOCOL_COMPLIANCE,
                    severity=ValidationSeverity.CRITICAL,
                ),
                TestCase(
                    name="invalid_json_rpc_version",
                    description="Test response to invalid JSON-RPC version",
                    method="a2a.ping",
                    params=None,
                    category=ValidationCategory.PROTOCOL_COMPLIANCE,
                    severity=ValidationSeverity.HIGH,
                    should_fail=True,
                    metadata={"override_jsonrpc": "1.0"},
                ),
                TestCase(
                    name="missing_method_field",
                    description="Test response to missing method field",
                    method="",
                    params=None,
                    category=ValidationCategory.PROTOCOL_COMPLIANCE,
                    severity=ValidationSeverity.CRITICAL,
                    should_fail=True,
                ),
            ]
        )

        # Generate method-specific tests
        for method in methods:
            test_cases.extend(
                [
                    TestCase(
                        name=f"method_{method}_basic_call",
                        description=f"Basic call to {method}",
                        method=method,
                        params=None,
                        category=ValidationCategory.METHOD_DISCOVERY,
                        severity=ValidationSeverity.MEDIUM,
                    ),
                    TestCase(
                        name=f"method_{method}_with_empty_params",
                        description=f"Call {method} with empty parameters",
                        method=method,
                        params={},
                        category=ValidationCategory.METHOD_DISCOVERY,
                        severity=ValidationSeverity.LOW,
                    ),
                ]
            )

        return test_cases

    def generate_error_handling_tests(self, methods: List[str]) -> List[TestCase]:
        """Generate error handling test cases."""
        test_cases = []

        # Generic error handling tests
        test_cases.extend(
            [
                TestCase(
                    name="method_not_found",
                    description="Test method not found error",
                    method="nonexistent.method",
                    params=None,
                    category=ValidationCategory.ERROR_HANDLING,
                    severity=ValidationSeverity.HIGH,
                    should_fail=True,
                ),
                TestCase(
                    name="invalid_params_type",
                    description="Test invalid parameter types",
                    method="a2a.ping",
                    params="invalid_params_should_be_object_or_array",
                    category=ValidationCategory.ERROR_HANDLING,
                    severity=ValidationSeverity.MEDIUM,
                    should_fail=True,
                ),
                TestCase(
                    name="malformed_request_missing_jsonrpc",
                    description="Test malformed request without jsonrpc field",
                    method="a2a.ping",
                    params=None,
                    category=ValidationCategory.ERROR_HANDLING,
                    severity=ValidationSeverity.CRITICAL,
                    should_fail=True,
                    metadata={"remove_jsonrpc": True},
                ),
            ]
        )

        return test_cases

    def generate_performance_tests(self, methods: List[str]) -> List[TestCase]:
        """Generate performance benchmark tests."""
        test_cases = []

        if methods:
            # Use first available method for performance testing
            method = methods[0]
            test_cases.extend(
                [
                    TestCase(
                        name="response_time_benchmark",
                        description="Measure typical response time",
                        method=method,
                        params=None,
                        category=ValidationCategory.PERFORMANCE,
                        severity=ValidationSeverity.INFO,
                        timeout_ms=1000,
                    ),
                    TestCase(
                        name="concurrent_requests_test",
                        description="Test concurrent request handling",
                        method=method,
                        params=None,
                        category=ValidationCategory.PERFORMANCE,
                        severity=ValidationSeverity.MEDIUM,
                        metadata={"concurrent_count": 5},
                    ),
                ]
            )

        return test_cases

    async def generate_test_suite(
        self, suite_name: str = "A2A Protocol Compliance"
    ) -> TestSuite:
        """Generate comprehensive A2A test suite."""
        # Discover available methods
        methods = await self.discover_agent_capabilities()

        # Generate all test categories
        test_cases = []
        test_cases.extend(self.generate_protocol_compliance_tests(methods))
        test_cases.extend(self.generate_error_handling_tests(methods))
        test_cases.extend(self.generate_performance_tests(methods))

        return TestSuite(
            name=suite_name,
            description="Comprehensive A2A protocol compliance and functionality tests",
            test_cases=test_cases,
        )


class ValidationExecutionEngine:
    """Executes A2A validation suites and reports results."""

    def __init__(self, client: A2AValidationClient) -> None:
        self.client = client

    async def execute_test_case(self, test_case: TestCase) -> TestExecutionResult:
        """Execute a single test case."""
        import time

        start_time = time.time()

        try:
            # Execute the A2A method call
            if test_case.metadata.get("concurrent_count", 0) > 1:
                # Execute concurrent requests
                concurrent_count = test_case.metadata["concurrent_count"]
                methods = [
                    {"method": test_case.method, "params": test_case.params}
                ] * concurrent_count
                results = await self.client.batch_call(methods)
                a2a_result = results[0] if results else None
            else:
                # Single request
                a2a_result = await self.client.call_method(
                    test_case.method,
                    test_case.params,
                    validate_request=True,
                    validate_response=True,
                )

            execution_time_ms = (time.time() - start_time) * 1000

            # Determine if test passed
            passed: bool
            error_message: Optional[str]
            if a2a_result is None:
                passed = False
                error_message = "No result received from test execution"
            elif test_case.should_fail:
                # Test expects failure
                passed = bool(
                    a2a_result.error is not None
                    or not a2a_result.validation_result.is_valid
                    or (a2a_result.status_code and a2a_result.status_code >= 400)
                )
                error_message = (
                    None if passed else "Expected test to fail but it succeeded"
                )
            else:
                # Test expects success
                passed = bool(
                    a2a_result.error is None
                    and a2a_result.validation_result.is_valid
                    and (a2a_result.status_code is None or a2a_result.status_code < 400)
                )
                error_message = (
                    None
                    if passed
                    else (
                        (a2a_result.error if a2a_result else "Unknown error")
                        or (
                            "; ".join(a2a_result.validation_result.errors)
                            if a2a_result
                            else "No validation details"
                        )
                    )
                )

            # Check timeout
            if execution_time_ms > test_case.timeout_ms:
                passed = False
                error_message = f"Test exceeded timeout of {test_case.timeout_ms}ms"

            return TestExecutionResult(
                test_case=test_case,
                a2a_result=a2a_result,
                passed=passed,
                execution_time_ms=execution_time_ms,
                error_message=error_message,
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000

            # Create error result
            from .client import A2AValidationResult
            from .validator import ValidationResult

            a2a_result = A2AValidationResult(
                method=test_case.method,
                params=test_case.params,
                response=None,
                validation_result=ValidationResult(
                    is_valid=False,
                    errors=[f"Test execution exception: {e}"],
                    warnings=[],
                ),
                response_time_ms=execution_time_ms,
                error=str(e),
            )

            return TestExecutionResult(
                test_case=test_case,
                a2a_result=a2a_result,
                passed=test_case.should_fail,  # If we expected failure, exception might be OK
                execution_time_ms=execution_time_ms,
                error_message=str(e),
            )

    async def execute_test_suite(self, test_suite: TestSuite) -> TestSuiteResult:
        """Execute entire test suite."""
        import time

        start_time = time.time()

        # Run setup if provided
        if test_suite.setup:
            await test_suite.setup()

        try:
            # Execute all test cases
            results = []
            for test_case in test_suite.test_cases:
                result = await self.execute_test_case(test_case)
                results.append(result)

            execution_time_ms = (time.time() - start_time) * 1000

            # Calculate summary statistics
            total_tests = len(results)
            passed_tests = sum(1 for r in results if r.passed)
            failed_tests = total_tests - passed_tests

            # Generate detailed summary
            summary: Dict[str, Any] = {
                "pass_rate": (passed_tests / total_tests * 100)
                if total_tests > 0
                else 0,
                "avg_response_time_ms": sum(r.execution_time_ms for r in results)
                / total_tests
                if total_tests > 0
                else 0,
                "category_breakdown": {},
                "severity_breakdown": {},
            }

            # Category and severity breakdowns
            for result in results:
                category = result.test_case.category.value
                severity = result.test_case.severity.value

                if category not in summary["category_breakdown"]:
                    summary["category_breakdown"][category] = {"passed": 0, "failed": 0}
                if severity not in summary["severity_breakdown"]:
                    summary["severity_breakdown"][severity] = {"passed": 0, "failed": 0}

                if result.passed:
                    summary["category_breakdown"][category]["passed"] += 1
                    summary["severity_breakdown"][severity]["passed"] += 1
                else:
                    summary["category_breakdown"][category]["failed"] += 1
                    summary["severity_breakdown"][severity]["failed"] += 1

            return TestSuiteResult(
                test_suite=test_suite,
                results=results,
                total_tests=total_tests,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                execution_time_ms=execution_time_ms,
                summary=summary,
            )

        finally:
            # Run teardown if provided
            if test_suite.teardown:
                await test_suite.teardown()

    def generate_report(
        self, suite_result: TestSuiteResult, format_type: str = "text"
    ) -> str:
        """Generate test execution report."""
        if format_type == "json":
            return self._generate_json_report(suite_result)
        elif format_type == "junit":
            return self._generate_junit_report(suite_result)
        else:
            return self._generate_text_report(suite_result)

    def _generate_text_report(self, suite_result: TestSuiteResult) -> str:
        """Generate human-readable text report."""
        report = []
        report.append(f"A2A Test Suite Report: {suite_result.test_suite.name}")
        report.append("=" * 60)
        report.append(f"Total Tests: {suite_result.total_tests}")
        report.append(f"Passed: {suite_result.passed_tests}")
        report.append(f"Failed: {suite_result.failed_tests}")
        report.append(f"Pass Rate: {suite_result.summary['pass_rate']:.1f}%")
        report.append(f"Execution Time: {suite_result.execution_time_ms:.1f}ms")
        report.append("")

        # Failed tests details
        failed_results = [r for r in suite_result.results if not r.passed]
        if failed_results:
            report.append("Failed Tests:")
            report.append("-" * 20)
            for result in failed_results:
                report.append(f"• {result.test_case.name}: {result.error_message}")
            report.append("")

        # Category breakdown
        report.append("Results by Category:")
        report.append("-" * 20)
        for category, stats in suite_result.summary["category_breakdown"].items():
            total = stats["passed"] + stats["failed"]
            pass_rate = (stats["passed"] / total * 100) if total > 0 else 0
            report.append(f"• {category}: {stats['passed']}/{total} ({pass_rate:.1f}%)")

        return "\n".join(report)

    def _generate_json_report(self, suite_result: TestSuiteResult) -> str:
        """Generate JSON report."""
        report_data: Dict[str, Any] = {
            "test_suite": suite_result.test_suite.name,
            "summary": {
                "total_tests": suite_result.total_tests,
                "passed_tests": suite_result.passed_tests,
                "failed_tests": suite_result.failed_tests,
                "execution_time_ms": suite_result.execution_time_ms,
                **suite_result.summary,
            },
            "test_results": [],
        }

        for result in suite_result.results:
            report_data["test_results"].append(
                {
                    "name": result.test_case.name,
                    "description": result.test_case.description,
                    "method": result.test_case.method,
                    "category": result.test_case.category.value,
                    "severity": result.test_case.severity.value,
                    "passed": result.passed,
                    "execution_time_ms": result.execution_time_ms,
                    "error_message": result.error_message,
                    "response_time_ms": result.a2a_result.response_time_ms
                    if result.a2a_result
                    else None,
                    "status_code": result.a2a_result.status_code
                    if result.a2a_result
                    else None,
                }
            )

        return json.dumps(report_data, indent=2)

    def _generate_junit_report(self, suite_result: TestSuiteResult) -> str:
        """Generate JUnit XML report."""
        from xml.etree.ElementTree import Element, SubElement, tostring

        testsuites = Element("testsuites")
        testsuite = SubElement(testsuites, "testsuite")
        testsuite.set("name", suite_result.test_suite.name)
        testsuite.set("tests", str(suite_result.total_tests))
        testsuite.set("failures", str(suite_result.failed_tests))
        testsuite.set("time", str(suite_result.execution_time_ms / 1000))

        for result in suite_result.results:
            testcase = SubElement(testsuite, "testcase")
            testcase.set("classname", result.test_case.category.value)
            testcase.set("name", result.test_case.name)
            testcase.set("time", str(result.execution_time_ms / 1000))

            if not result.passed:
                failure = SubElement(testcase, "failure")
                failure.set("message", result.error_message or "Test failed")
                failure.text = result.error_message or "No detailed error message"

        return tostring(testsuites, encoding="unicode")
