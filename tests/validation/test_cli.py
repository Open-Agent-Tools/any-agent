"""Tests for A2A validation CLI."""

from unittest.mock import patch, MagicMock, AsyncMock
from click.testing import CliRunner
import json
import tempfile
from pathlib import Path

from any_agent.validation.cli import cli, _format_text_report, _format_junit_report


class TestCLI:
    """Test A2A validation CLI functionality."""

    def test_cli_help(self):
        """Test CLI help command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "A2A Protocol Validation Harness" in result.output

    @patch("any_agent.validation.cli.A2AMessageValidator")
    def test_validate_command_success(self, mock_validator_class):
        """Test validate command with successful tests."""
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator

        # Mock successful test results
        mock_results = {
            "success": True,
            "summary": {"total": 3, "passed": 3, "failed": 0, "duration_ms": 1500.0},
            "validations": [
                {
                    "scenario": "agent_card_discovery",
                    "success": True,
                    "duration_ms": 15.0,
                    "details": {"agent_name": "test"},
                },
                {
                    "scenario": "client_connection",
                    "success": True,
                    "duration_ms": 10.0,
                    "details": {"connection": "ok"},
                },
                {
                    "scenario": "basic_message_exchange",
                    "success": True,
                    "duration_ms": 200.0,
                    "details": {"messages": 1},
                },
            ],
        }

        mock_validator.validate_agent_a2a_protocol = AsyncMock(
            return_value=mock_results
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["validate", "8080"])

        assert result.exit_code == 0
        assert "Overall Status: PASSED" in result.output
        assert "3 passed, 0 failed" in result.output
        mock_validator.validate_agent_a2a_protocol.assert_called_once_with(8080)

    @patch("any_agent.validation.cli.A2AMessageValidator")
    def test_validate_command_failure(self, mock_validator_class):
        """Test validate command with failed tests."""
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator

        # Mock failed test results
        mock_results = {
            "success": False,
            "summary": {"total": 3, "passed": 1, "failed": 2, "duration_ms": 800.0},
            "validations": [
                {
                    "scenario": "agent_card_discovery",
                    "success": False,
                    "duration_ms": 5.0,
                    "details": {},
                    "error": "Agent card not found",
                },
                {
                    "scenario": "client_connection",
                    "success": True,
                    "duration_ms": 10.0,
                    "details": {"connection": "ok"},
                },
                {
                    "scenario": "basic_message_exchange",
                    "success": False,
                    "duration_ms": 100.0,
                    "details": {},
                    "error": "Message timeout",
                },
            ],
        }

        mock_validator.validate_agent_a2a_protocol = AsyncMock(
            return_value=mock_results
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["validate", "8080"])

        assert result.exit_code == 1
        assert "Overall Status: FAILED" in result.output
        assert "1 passed, 2 failed" in result.output

    @patch("any_agent.validation.cli.A2AMessageValidator")
    def test_validate_command_with_timeout(self, mock_validator_class):
        """Test validate command with custom timeout."""
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator

        mock_results = {
            "success": True,
            "summary": {"total": 0, "passed": 0, "failed": 0, "duration_ms": 0},
            "validations": [],
        }

        mock_validator.validate_agent_a2a_protocol = AsyncMock(
            return_value=mock_results
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["validate", "8080", "--timeout", "60"])

        assert result.exit_code == 0
        mock_validator_class.assert_called_once_with(timeout=60)

    @patch("any_agent.validation.cli.A2AMessageValidator")
    def test_validate_command_verbose(self, mock_validator_class):
        """Test validate command with verbose output."""
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator

        mock_results = {
            "success": True,
            "summary": {"total": 1, "passed": 1, "failed": 0, "duration_ms": 100.0},
            "validations": [
                {
                    "scenario": "agent_card_discovery",
                    "success": True,
                    "duration_ms": 15.0,
                    "details": {"agent_name": "test"},
                }
            ],
        }

        mock_validator.validate_agent_a2a_protocol = AsyncMock(
            return_value=mock_results
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["validate", "8080", "--verbose"])

        assert result.exit_code == 0
        assert "Testing agent on port 8080" in result.output

    @patch("any_agent.validation.cli.A2AMessageValidator")
    def test_validate_command_json_output(self, mock_validator_class):
        """Test validate command with JSON output format."""
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator

        mock_results = {
            "success": True,
            "summary": {"total": 0, "passed": 0, "failed": 0, "duration_ms": 0},
            "validations": [],
        }

        mock_validator.validate_agent_a2a_protocol = AsyncMock(
            return_value=mock_results
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["validate", "8080", "--format", "json"])

        assert result.exit_code == 0
        # Should be valid JSON
        json.loads(result.output)

    @patch("any_agent.validation.cli.A2AMessageValidator")
    def test_validate_command_save_to_file(self, mock_validator_class):
        """Test validate command saving results to file."""
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator

        mock_results = {
            "success": True,
            "summary": {"total": 0, "passed": 0, "failed": 0, "duration_ms": 0},
            "validations": [],
        }

        mock_validator.validate_agent_a2a_protocol = AsyncMock(
            return_value=mock_results
        )

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            output_file = f.name

        try:
            runner = CliRunner()
            result = runner.invoke(
                cli, ["validate", "8080", "--format", "json", "--output", output_file]
            )

            assert result.exit_code == 0
            assert f"Results saved to: {output_file}" in result.output

            # Check file was created and contains valid JSON
            with open(output_file, "r") as f:
                saved_data = json.load(f)
            assert saved_data == mock_results

        finally:
            Path(output_file).unlink(missing_ok=True)

    @patch("any_agent.validation.cli.A2AMessageValidator")
    def test_validate_command_sdk_not_available(self, mock_validator_class):
        """Test validate command when A2A SDK is not available."""
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator

        mock_results = {
            "success": False,
            "error": "a2a-sdk not available - install with: pip install a2a-sdk>=0.1.0",
            "summary": {"total": 0, "passed": 0, "failed": 0, "duration_ms": 0},
            "validations": [],
        }

        mock_validator.validate_agent_a2a_protocol = AsyncMock(
            return_value=mock_results
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["validate", "8080"])

        assert result.exit_code == 1  # Failed tests exit code
        assert "a2a-sdk not available" in result.output

    def test_format_text_output_success(self):
        """Test text output formatting for successful results."""
        results = {
            "success": True,
            "summary": {"total": 2, "passed": 2, "failed": 0, "duration_ms": 100.0},
            "validations": [
                {
                    "scenario": "test1",
                    "success": True,
                    "duration_ms": 50.0,
                    "details": {},
                },
                {
                    "scenario": "test2",
                    "success": True,
                    "duration_ms": 50.0,
                    "details": {},
                },
            ],
        }

        output = _format_text_report(results, verbose=False)
        assert "Overall Status: PASSED" in output
        assert "2 passed, 0 failed" in output

    def test_format_text_output_failure(self):
        """Test text output formatting for failed results."""
        results = {
            "success": False,
            "summary": {"total": 2, "passed": 1, "failed": 1, "duration_ms": 100.0},
            "validations": [
                {
                    "scenario": "test1",
                    "success": True,
                    "duration_ms": 50.0,
                    "details": {},
                },
                {
                    "scenario": "test2",
                    "success": False,
                    "duration_ms": 50.0,
                    "details": {},
                    "error": "Test failed",
                },
            ],
        }

        output = _format_text_report(results, verbose=False)
        assert "Overall Status: FAILED" in output
        assert "1 passed, 1 failed" in output

    def test_format_json_output(self):
        """Test JSON output formatting."""
        results = {
            "success": True,
            "summary": {"total": 0, "passed": 0, "failed": 0},
            "validations": [],
        }

        # JSON output is just json.dumps, so test it directly
        output = json.dumps(results, indent=2)
        parsed = json.loads(output)
        assert parsed == results

    def test_format_junit_xml_success(self):
        """Test JUnit XML output formatting for successful tests."""
        results = {
            "success": True,
            "summary": {"total": 2, "passed": 2, "failed": 0, "duration_ms": 1500.0},
            "validations": [
                {
                    "scenario": "test1",
                    "success": True,
                    "duration_ms": 750.0,
                    "details": {},
                },
                {
                    "scenario": "test2",
                    "success": True,
                    "duration_ms": 750.0,
                    "details": {},
                },
            ],
        }

        output = _format_junit_report(results)
        assert '<testsuite name="A2A Protocol Validation"' in output
        assert 'tests="2"' in output
        assert 'failures="0"' in output
        assert 'time="1.5"' in output
        assert '<testcase name="test1"' in output
        assert '<testcase name="test2"' in output

    def test_format_junit_xml_failure(self):
        """Test JUnit XML output formatting for failed tests."""
        results = {
            "success": False,
            "summary": {"total": 2, "passed": 1, "failed": 1, "duration_ms": 1000.0},
            "validations": [
                {
                    "scenario": "test1",
                    "success": True,
                    "duration_ms": 500.0,
                    "details": {},
                },
                {
                    "scenario": "test2",
                    "success": False,
                    "duration_ms": 500.0,
                    "details": {},
                    "error": "Test failed",
                },
            ],
        }

        output = _format_junit_report(results)
        assert '<testsuite name="A2A Protocol Validation"' in output
        assert 'tests="2"' in output
        assert 'failures="1"' in output
        assert '<failure message="Test failed">' in output
