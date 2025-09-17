"""Command Line Interface for A2A Validation Harness."""

import asyncio
import sys
from pathlib import Path
from typing import Optional
import click
import yaml
import json

from .client import A2AValidationClient, A2AValidationConfig
from .engine import ValidationDiscoveryEngine, ValidationExecutionEngine
from .a2a_message_validator import A2AMessageValidator
from any_agent import __version__


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """A2A Protocol Validation Harness - Universal validation for Agent-to-Agent communication."""
    pass


@cli.command(name="test")
@click.argument("endpoint", default="http://localhost:8080")
@click.option(
    "--config", "-c", type=click.Path(exists=True), help="Configuration file path"
)
@click.option("--auth-token", help="Authentication token")
@click.option("--auth-type", type=click.Choice(["bearer", "api_key"]), default="bearer")
@click.option("--timeout", type=float, default=30.0, help="Request timeout in seconds")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "junit"]),
    default="text",
    help="Output format",
)
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def test_a2a_protocol(
    endpoint: str,
    config: Optional[str],
    auth_token: Optional[str],
    auth_type: str,
    timeout: float,
    output_format: str,
    output: Optional[str],
    verbose: bool,
) -> None:
    """Run comprehensive A2A protocol compliance tests."""
    asyncio.run(
        _run_tests(
            endpoint,
            config,
            auth_token,
            auth_type,
            timeout,
            output_format,
            output,
            verbose,
        )
    )


async def _run_tests(
    endpoint: str,
    config_path: Optional[str],
    auth_token: Optional[str],
    auth_type: str,
    timeout: float,
    output_format: str,
    output_path: Optional[str],
    verbose: bool,
) -> None:
    """Run A2A tests asynchronously."""
    # Load configuration
    test_config = _load_config(endpoint, config_path, auth_token, auth_type, timeout)

    if verbose:
        click.echo(f"Testing A2A endpoint: {test_config.endpoint}")
        click.echo(f"Timeout: {test_config.timeout}s")
        click.echo(f"Auth type: {test_config.auth_type}")

    try:
        async with A2AValidationClient(test_config) as client:
            # Validate endpoint health
            if verbose:
                click.echo("Checking endpoint health...")

            health_result = await client.validate_endpoint_health()
            if health_result.error:
                click.echo(
                    f"❌ Endpoint health check failed: {health_result.error}", err=True
                )
                sys.exit(1)

            if verbose:
                click.echo("✅ Endpoint is healthy")

            # Discover and execute tests
            discovery_engine = ValidationDiscoveryEngine(client)
            execution_engine = ValidationExecutionEngine(client)

            if verbose:
                click.echo("Generating test suite...")

            test_suite = await discovery_engine.generate_test_suite()

            if verbose:
                click.echo(f"Generated {len(test_suite.test_cases)} test cases")
                click.echo("Executing tests...")

            result = await execution_engine.execute_test_suite(test_suite)

            # Generate report
            report = execution_engine.generate_report(result, output_format)

            # Output report
            if output_path:
                with open(output_path, "w") as f:
                    f.write(report)
                click.echo(f"Report saved to: {output_path}")
            else:
                click.echo(report)

            # Exit with failure code if tests failed
            if result.failed_tests > 0:
                sys.exit(1)

    except Exception as execution_error:
        click.echo(f"❌ Test execution failed: {execution_error}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("endpoint", default="http://localhost:8080")
@click.option(
    "--config", "-c", type=click.Path(exists=True), help="Configuration file path"
)
@click.option("--auth-token", help="Authentication token")
@click.option("--auth-type", type=click.Choice(["bearer", "api_key"]), default="bearer")
@click.option("--timeout", type=float, default=30.0, help="Request timeout in seconds")
def discover(
    endpoint: str,
    config: Optional[str],
    auth_token: Optional[str],
    auth_type: str,
    timeout: float,
) -> None:
    """Discover available A2A methods and capabilities."""
    asyncio.run(_discover_methods(endpoint, config, auth_token, auth_type, timeout))


async def _discover_methods(
    endpoint: str,
    config_path: Optional[str],
    auth_token: Optional[str],
    auth_type: str,
    timeout: float,
) -> None:
    """Discover A2A methods asynchronously."""
    test_config = _load_config(endpoint, config_path, auth_token, auth_type, timeout)

    try:
        async with A2AValidationClient(test_config) as client:
            discovery_engine = ValidationDiscoveryEngine(client)

            click.echo(f"Discovering methods on: {endpoint}")

            # Get agent card
            agent_card_result = await client.get_agent_card()
            if agent_card_result.response:
                click.echo("\n📋 Agent Card:")
                agent_card = agent_card_result.response.get("result", {})
                click.echo(f"  Name: {agent_card.get('name', 'Unknown')}")
                click.echo(f"  Version: {agent_card.get('version', 'Unknown')}")

                if "capabilities" in agent_card:
                    click.echo(f"  Capabilities: {len(agent_card['capabilities'])}")
                    for cap in agent_card["capabilities"]:
                        method = cap.get("method", "unknown")
                        description = cap.get("description", "")
                        click.echo(f"    • {method}: {description}")

            # Discover methods
            methods = await discovery_engine.discover_agent_capabilities()

            if methods:
                click.echo(f"\n🔍 Discovered Methods ({len(methods)}):")
                for method in methods:
                    click.echo(f"  • {method}")
            else:
                click.echo("\n⚠️  No methods discovered")

    except Exception as discovery_error:
        click.echo(f"❌ Discovery failed: {discovery_error}", err=True)
        sys.exit(1)


@cli.command(name="call")
@click.argument("endpoint", default="http://localhost:8080")
@click.argument("method")
@click.option("--params", help="JSON parameters for the method call")
@click.option(
    "--config", "-c", type=click.Path(exists=True), help="Configuration file path"
)
@click.option("--auth-token", help="Authentication token")
@click.option("--auth-type", type=click.Choice(["bearer", "api_key"]), default="bearer")
@click.option("--timeout", type=float, default=30.0, help="Request timeout in seconds")
@click.option(
    "--validate/--no-validate", default=True, help="Validate JSON-RPC compliance"
)
def call_a2a_method(
    endpoint: str,
    method: str,
    params: Optional[str],
    config: Optional[str],
    auth_token: Optional[str],
    auth_type: str,
    timeout: float,
    validate: bool,
) -> None:
    """Call a specific A2A method."""
    asyncio.run(
        _call_a2a_method(
            endpoint, method, params, config, auth_token, auth_type, timeout, validate
        )
    )


async def _call_a2a_method(
    endpoint: str,
    method: str,
    params_str: Optional[str],
    config_path: Optional[str],
    auth_token: Optional[str],
    auth_type: str,
    timeout: float,
    validate: bool,
) -> None:
    """Call A2A method asynchronously."""
    test_config = _load_config(endpoint, config_path, auth_token, auth_type, timeout)

    # Parse parameters
    params = None
    if params_str:
        try:
            params = json.loads(params_str)
        except json.JSONDecodeError as e:
            click.echo(f"❌ Invalid JSON parameters: {e}", err=True)
            sys.exit(1)

    try:
        async with A2AValidationClient(test_config) as client:
            click.echo(f"Calling {method} on {endpoint}")
            if params:
                click.echo(f"Parameters: {json.dumps(params, indent=2)}")

            result = await client.call_method(
                method, params, validate_request=validate, validate_response=validate
            )

            # Display results
            click.echo(f"\n⏱️  Response Time: {result.response_time_ms:.1f}ms")
            click.echo(f"🔗 Status Code: {result.status_code}")

            if validate:
                if result.validation_result.is_valid:
                    click.echo("✅ Validation: PASSED")
                else:
                    click.echo("❌ Validation: FAILED")
                    for error in result.validation_result.errors:
                        click.echo(f"  • {error}")

                if result.validation_result.warnings:
                    click.echo("⚠️  Warnings:")
                    for warning in result.validation_result.warnings:
                        click.echo(f"  • {warning}")

            if result.response:
                click.echo("\n📄 Response:")
                click.echo(json.dumps(result.response, indent=2))

            if result.error:
                click.echo(f"\n❌ Error: {result.error}")
                sys.exit(1)

    except Exception as call_error:
        click.echo(f"❌ Method call failed: {call_error}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--endpoint", default="http://localhost:8080")
@click.option("--auth-type", type=click.Choice(["bearer", "api_key"]), default="bearer")
@click.option("--output", "-o", type=click.Path(), default="a2a-test-config.yaml")
def init_config(endpoint: str, auth_type: str, output: str) -> None:
    """Generate a sample A2A test configuration file."""
    config = {
        "endpoint": endpoint,
        "timeout": 30.0,
        "auth_type": auth_type,
        "verify_ssl": True,
        "headers": {"User-Agent": "A2A-Testing-Harness/1.0"},
        "test_suites": {
            "compliance": {
                "enabled": True,
                "categories": [
                    "protocol_compliance",
                    "method_discovery",
                    "error_handling",
                ],
            },
            "performance": {
                "enabled": False,
                "response_time_threshold_ms": 1000,
                "concurrent_requests": 5,
            },
        },
    }

    with open(output, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    click.echo(f"✅ Configuration file created: {output}")
    click.echo("Edit the file to customize your test settings.")


def _load_config(
    endpoint: str,
    config_path: Optional[str],
    auth_token: Optional[str],
    auth_type: str,
    timeout: float,
) -> A2AValidationConfig:
    """Load configuration from file and command line options."""
    config_data = {
        "endpoint": endpoint,
        "timeout": timeout,
        "auth_type": auth_type,
        "auth_token": auth_token,
    }

    if config_path:
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, "r") as f:
                if config_file.suffix.lower() in [".yaml", ".yml"]:
                    file_config = yaml.safe_load(f) or {}
                else:
                    file_config = json.load(f)

            # Merge file config (file config as base, CLI options override)
            for key, value in file_config.items():
                if key not in config_data or config_data[key] is None:
                    if key in [
                        "endpoint",
                        "timeout",
                        "auth_type",
                        "auth_token",
                        "verify_ssl",
                        "headers",
                    ]:
                        config_data[key] = value

    # Remove None values
    config_data = {k: v for k, v in config_data.items() if v is not None}

    return A2AValidationConfig(**config_data)  # type: ignore[arg-type]


@cli.command(name="validate")
@click.argument("port", type=int, default=8080)
@click.option(
    "--timeout", type=int, default=30, help="Timeout for A2A operations in seconds"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "junit"]),
    default="text",
    help="Output format",
)
@click.option("--output", "-o", type=click.Path(), help="Save results to file")
def validate_agent_deployment(
    port: int, timeout: int, verbose: bool, output_format: str, output: Optional[str]
) -> None:
    """Run comprehensive A2A protocol validation tests against a deployed agent.

    This command runs the 3 core A2A validation tests:
    1. Agent card discovery and validation
    2. A2A client connection testing
    3. Basic message exchange verification

    Examples:
      a2a-test validate 8080                    # Test agent on port 8080
      a2a-test validate 3000 --verbose         # Test with detailed output
      a2a-test validate 8080 --format json -o results.json  # Save JSON report
    """
    asyncio.run(_run_validation(port, timeout, verbose, output_format, output))


async def _run_validation(
    port: int,
    timeout: int,
    verbose: bool,
    output_format: str,
    output_path: Optional[str],
) -> None:
    """Run A2A validation tests asynchronously."""
    if verbose:
        click.echo("🚀 A2A Protocol Validation")
        click.echo(f"📡 Testing agent on port {port}")
        click.echo(f"⏱️  Timeout: {timeout}s")
        click.echo()

    validator = A2AMessageValidator(timeout=timeout)

    try:
        # Run the comprehensive tests
        results = await validator.validate_agent_a2a_protocol(port)

        # Format and display results
        if output_format == "json":
            report = json.dumps(results, indent=2)
        elif output_format == "junit":
            report = _format_junit_report(results)
        else:  # text format
            report = _format_text_report(results, verbose)

        # Output results
        if output_path:
            with open(output_path, "w") as f:
                f.write(report)
            click.echo(f"📄 Results saved to: {output_path}")
        else:
            click.echo(report)

        # Exit with appropriate code
        if not results.get("success", False):
            sys.exit(1)

    except Exception as validation_error:
        click.echo(f"❌ Validation failed: {validation_error}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


def _format_text_report(results: dict, verbose: bool) -> str:
    """Format validation results as readable text."""
    lines = []

    # Header
    lines.append("🧪 A2A Protocol Validation Report")
    lines.append("=" * 40)

    # Summary
    success = results.get("success", False)
    summary = results.get("summary", {})

    status_icon = "✅" if success else "❌"
    lines.append(f"{status_icon} Overall Status: {'PASSED' if success else 'FAILED'}")
    lines.append(
        f"📊 Tests: {summary.get('total', 0)} total, {summary.get('passed', 0)} passed, {summary.get('failed', 0)} failed"
    )
    lines.append(f"⏱️  Duration: {summary.get('duration_ms', 0):.1f}ms")
    lines.append("")

    # Individual validation results
    validations = results.get("validations", [])
    if validations:
        lines.append("📋 Validation Details:")
        for validation in validations:
            validation_status = "✅" if validation.get("success", False) else "❌"
            scenario = validation.get("scenario", "unknown")
            duration = validation.get("duration_ms", 0)
            lines.append(f"  {validation_status} {scenario}: {duration:.1f}ms")

            if verbose and validation.get("error"):
                lines.append(f"      Error: {validation['error']}")

            if verbose and validation.get("details"):
                details = validation["details"]
                for key, value in details.items():
                    lines.append(f"      {key}: {value}")
        lines.append("")

    # Errors (if any)
    if not success and results.get("error"):
        lines.append("❌ Error Details:")
        lines.append(f"   {results['error']}")
        lines.append("")

    return "\n".join(lines)


def _format_junit_report(results: dict) -> str:
    """Format validation results as JUnit XML."""
    from xml.etree.ElementTree import Element, SubElement, tostring

    # Create root testsuite element
    summary = results.get("summary", {})
    testsuite = Element(
        "testsuite",
        {
            "name": "A2A Protocol Validation",
            "tests": str(summary.get("total", 0)),
            "failures": str(summary.get("failed", 0)),
            "time": str(summary.get("duration_ms", 0) / 1000),
        },
    )

    # Add individual validation cases
    validations = results.get("validations", [])
    for validation in validations:
        testcase = SubElement(
            testsuite,
            "testcase",
            {
                "name": validation.get("scenario", "unknown"),
                "time": str(validation.get("duration_ms", 0) / 1000),
            },
        )

        if not validation.get("success", False):
            failure = SubElement(
                testcase,
                "failure",
                {"message": validation.get("error", "Validation failed")},
            )
            failure.text = str(validation.get("details", {}))

    return tostring(testsuite, encoding="unicode")


if __name__ == "__main__":
    cli()
