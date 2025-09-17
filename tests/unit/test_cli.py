"""Tests for CLI interface."""

import os
from click.testing import CliRunner
from any_agent.cli import main


def test_cli_dry_run():
    """Test CLI dry run mode."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Create a test agent directory
        os.makedirs("test_agent")
        with open("test_agent/a2a_app.py", "w") as f:
            f.write("# Test agent file")

        result = runner.invoke(
            main, ["test_agent/a2a_app.py", "--dry-run", "--verbose"]
        )

        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert "Any Agent Framework" in result.output


def test_cli_help():
    """Test CLI help message."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "Universal AI Agent Containerization Framework" in result.output
    assert "--framework" in result.output
    assert "--port" in result.output
    assert "Google ADK" in result.output  # Should mention ADK in help


def test_cli_adk_framework_detection():
    """Test CLI with explicit ADK framework specification."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Create ADK-style agent directory
        os.makedirs("adk_test")
        with open("adk_test/__init__.py", "w") as f:
            f.write("# ADK Agent")
        with open("adk_test/agent.py", "w") as f:
            f.write("# ADK agent implementation")

        result = runner.invoke(main, ["adk_test", "--framework", "adk", "--dry-run"])

        assert result.exit_code == 0
        assert "DRY RUN" in result.output



def test_cli_invalid_path():
    """Test CLI with invalid agent path."""
    runner = CliRunner()

    result = runner.invoke(main, ["non_existent_path"])

    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_cli_invalid_framework():
    """Test CLI with invalid framework choice."""
    runner = CliRunner()

    result = runner.invoke(main, [".", "--framework", "invalid_framework"])

    assert result.exit_code != 0
    assert "Invalid value for" in result.output


def test_cli_port_validation():
    """Test CLI port validation."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        os.makedirs("test_agent")
        with open("test_agent/__init__.py", "w") as f:
            f.write("# Test agent")

        # Test low port (should show permission error)
        result = runner.invoke(main, ["test_agent", "--port", "22"])

        # Should exit with error and show helpful message
        assert result.exit_code == 0  # CLI shows error but doesn't crash
        assert "permission denied" in result.output.lower()


def test_cli_verbose_mode():
    """Test CLI verbose logging."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        os.makedirs("test_agent")
        with open("test_agent/__init__.py", "w") as f:
            f.write("# Test agent")

        result = runner.invoke(main, ["test_agent", "--verbose", "--dry-run"])

        assert result.exit_code == 0
        assert "DRY RUN" in result.output


def test_cli_removal_list_mode():
    """Test CLI removal list functionality."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        os.makedirs("test_agent")
        with open("test_agent/__init__.py", "w") as f:
            f.write("# Test agent")

        result = runner.invoke(main, ["test_agent", "--list"])

        assert result.exit_code == 0


def test_cli_protocol_specification():
    """Test CLI protocol specification."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        os.makedirs("test_agent")
        with open("test_agent/__init__.py", "w") as f:
            f.write("# Test agent")

        result = runner.invoke(main, ["test_agent", "--dry-run"])

        assert result.exit_code == 0
        assert "DRY RUN" in result.output


def test_cli_comprehensive_adk_workflow():
    """Test complete ADK workflow in dry-run mode."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Create ADK-like structure
        os.makedirs("my_adk_agent")
        with open("my_adk_agent/__init__.py", "w") as f:
            f.write("# ADK Agent Root")
        with open("my_adk_agent/agent.py", "w") as f:
            f.write("# Agent implementation")
        with open("my_adk_agent/requirements.txt", "w") as f:
            f.write("google-cloud-functions\n")

        result = runner.invoke(
            main,
            [
                "my_adk_agent",
                "--framework",
                "adk",
                "--port",
                "8080",
                "--agent-name",
                "comprehensive-test-agent",
                "--dry-run",
                "--verbose",
            ],
        )

        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert "my_adk_agent" in result.output


def test_cli_error_handling_coverage():
    """Test various error scenarios for comprehensive coverage."""
    runner = CliRunner()

    # Test with invalid agent-name format (empty)
    with runner.isolated_filesystem():
        os.makedirs("test_agent")
        with open("test_agent/__init__.py", "w") as f:
            f.write("# Test agent")

        result = runner.invoke(main, ["test_agent", "--agent-name", "", "--dry-run"])

        assert result.exit_code == 0  # Should handle gracefully
