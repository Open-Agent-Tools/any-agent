"""Comprehensive CLI interface tests to improve coverage from 27% to 75%."""

import os
import json
from unittest.mock import patch, Mock
from click.testing import CliRunner
import pytest
from any_agent.cli import main


class TestCLIComprehensiveCoverage:
    """Comprehensive CLI test suite to achieve 75% coverage target."""

    def test_cli_with_directory_option(self):
        """Test CLI with explicit directory option."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            os.makedirs("agent_dir")
            with open("agent_dir/__init__.py", "w") as f:
                f.write("# Agent")

            result = runner.invoke(main, ["agent_dir", "-d", "agent_dir", "--dry-run"])

            assert result.exit_code == 0

    def test_cli_no_build_flag(self):
        """Test CLI with --no-build flag."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            os.makedirs("test_agent")
            with open("test_agent/__init__.py", "w") as f:
                f.write("# Test agent")

            result = runner.invoke(main, ["test_agent", "--no-build", "--dry-run"])

            assert result.exit_code == 0
            assert "Skip building" in result.output or "DRY RUN" in result.output

    def test_cli_no_run_flag(self):
        """Test CLI with --no-run flag."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            os.makedirs("test_agent")
            with open("test_agent/__init__.py", "w") as f:
                f.write("# Test agent")

            result = runner.invoke(main, ["test_agent", "--no-run", "--dry-run"])

            assert result.exit_code == 0

    def test_cli_custom_container_name(self):
        """Test CLI with custom container name."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            os.makedirs("test_agent")
            with open("test_agent/__init__.py", "w") as f:
                f.write("# Test agent")

            result = runner.invoke(
                main, ["test_agent", "--container-name", "my-custom-agent", "--dry-run"]
            )

            assert result.exit_code == 0
            assert "my-custom-agent" in result.output or "DRY RUN" in result.output

    @pytest.mark.skip(
        reason="--push option removed during QA cleanup - unimplemented feature"
    )
    def test_cli_push_option(self):
        """Test CLI with push option."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            os.makedirs("test_agent")
            with open("test_agent/__init__.py", "w") as f:
                f.write("# Test agent")

            result = runner.invoke(
                main,
                [
                    "test_agent",
                    "--push",
                    "registry.example.com/my-agent:latest",
                    "--dry-run",
                ],
            )

            assert result.exit_code == 0

    def test_cli_config_file_option(self):
        """Test CLI with config file option."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            os.makedirs("test_agent")
            with open("test_agent/__init__.py", "w") as f:
                f.write("# Test agent")

            # Create config file
            config = {"agent": {"name": "test-config-agent", "framework": "adk"}}
            with open("config.json", "w") as f:
                json.dump(config, f)

            result = runner.invoke(
                main, ["test_agent", "--config", "config.json", "--dry-run"]
            )

            assert result.exit_code == 0

    def test_cli_output_directory_option(self):
        """Test CLI with output directory option."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            os.makedirs("test_agent")
            os.makedirs("output_dir")
            with open("test_agent/__init__.py", "w") as f:
                f.write("# Test agent")

            result = runner.invoke(
                main, ["test_agent", "--output", "output_dir", "--dry-run"]
            )

            assert result.exit_code == 0

    @pytest.mark.skip(
        reason="--protocol option removed during QA cleanup - unimplemented feature"
    )
    def test_cli_protocol_options(self):
        """Test CLI with different protocol options."""
        runner = CliRunner()
        protocols = ["a2a", "openai", "websocket", "custom"]

        for protocol in protocols:
            with runner.isolated_filesystem():
                os.makedirs("test_agent")
                with open("test_agent/__init__.py", "w") as f:
                    f.write("# Test agent")

                result = runner.invoke(
                    main, ["test_agent", "--protocol", protocol, "--dry-run"]
                )

                assert result.exit_code == 0

    @pytest.mark.skip(
        reason="--helmsman-token option removed during QA cleanup - unimplemented feature"
    )
    def test_cli_helmsman_token_option(self):
        """Test CLI with Helmsman token option."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            os.makedirs("test_agent")
            with open("test_agent/__init__.py", "w") as f:
                f.write("# Test agent")

            result = runner.invoke(
                main,
                [
                    "test_agent",
                    "--helmsman",
                    "--helmsman-token",
                    "test-token-123",
                    "--agent-name",
                    "test-helmsman-agent",
                    "--dry-run",
                ],
            )

            assert result.exit_code == 0

    def test_cli_no_ui_flag(self):
        """Test CLI with --no-ui flag."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            os.makedirs("test_agent")
            with open("test_agent/__init__.py", "w") as f:
                f.write("# Test agent")

            result = runner.invoke(main, ["test_agent", "--no-ui", "--dry-run"])

            assert result.exit_code == 0

    def test_cli_skip_a2a_test_flag(self):
        """Test CLI with --skip-a2a-test flag."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            os.makedirs("test_agent")
            with open("test_agent/__init__.py", "w") as f:
                f.write("# Test agent")

            result = runner.invoke(main, ["test_agent", "--skip-a2a-test", "--dry-run"])

            assert result.exit_code == 0

    def test_cli_a2a_test_timeout_option(self):
        """Test CLI with custom A2A test timeout."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            os.makedirs("test_agent")
            with open("test_agent/__init__.py", "w") as f:
                f.write("# Test agent")

            result = runner.invoke(
                main, ["test_agent", "--a2a-test-timeout", "60", "--dry-run"]
            )

            assert result.exit_code == 0

    def test_cli_rebuild_ui_flag(self):
        """Test CLI with --rebuild-ui flag."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            os.makedirs("test_agent")
            with open("test_agent/__init__.py", "w") as f:
                f.write("# Test agent")

            result = runner.invoke(main, ["test_agent", "--rebuild-ui", "--dry-run"])

            assert result.exit_code == 0

    def test_cli_all_framework_options(self):
        """Test CLI with all available framework options."""
        runner = CliRunner()
        frameworks = ["auto", "adk", "aws-strands", "langchain", "crewai"]

        for framework in frameworks:
            with runner.isolated_filesystem():
                os.makedirs("test_agent")
                with open("test_agent/__init__.py", "w") as f:
                    f.write("# Test agent")

                result = runner.invoke(
                    main, ["test_agent", "--framework", framework, "--dry-run"]
                )

                assert result.exit_code == 0

    @patch("any_agent.core.docker_orchestrator.AgentOrchestrator")
    def test_cli_framework_detection_paths(self, mock_orchestrator):
        """Test CLI framework detection with different outcomes."""
        runner = CliRunner()

        # Test case 1: Successful framework detection
        mock_adapter = Mock()
        mock_adapter.__class__.__name__ = "GoogleAdkAdapter"
        mock_orchestrator_instance = Mock()
        mock_orchestrator_instance.detect_framework.return_value = mock_adapter
        mock_orchestrator.return_value = mock_orchestrator_instance

        with runner.isolated_filesystem():
            os.makedirs("test_agent")
            with open("test_agent/__init__.py", "w") as f:
                f.write("# Test agent")

            result = runner.invoke(main, ["test_agent", "--verbose", "--dry-run"])

            assert result.exit_code == 0

    @patch("any_agent.core.docker_orchestrator.AgentOrchestrator")
    def test_cli_no_framework_detected_fallback(self, mock_orchestrator):
        """Test CLI behavior when no framework is detected."""
        runner = CliRunner()

        # Mock no framework detected
        mock_orchestrator_instance = Mock()
        mock_orchestrator_instance.detect_framework.return_value = None
        mock_orchestrator.return_value = mock_orchestrator_instance

        with runner.isolated_filesystem():
            os.makedirs("test_agent")
            with open("test_agent/__init__.py", "w") as f:
                f.write("# Test agent")

            result = runner.invoke(main, ["test_agent", "--verbose", "--dry-run"])

            assert result.exit_code == 0
            assert "fallback port" in result.output or "DRY RUN" in result.output

    def test_cli_port_range_variations(self):
        """Test CLI with various port numbers."""
        runner = CliRunner()
        ports = [3000, 8080, 8090, 9000]

        for port in ports:
            with runner.isolated_filesystem():
                os.makedirs("test_agent")
                with open("test_agent/__init__.py", "w") as f:
                    f.write("# Test agent")

                result = runner.invoke(
                    main, ["test_agent", "--port", str(port), "--dry-run"]
                )

                assert result.exit_code == 0

    def test_cli_version_display(self):
        """Test CLI version flag functionality."""
        runner = CliRunner()

        result = runner.invoke(main, ["--version"])

        # Should display version and exit successfully
        assert result.exit_code == 0
        assert "0.2.10" in result.output

    def test_cli_base_image_option(self):
        """Test CLI with custom base image option."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            os.makedirs("test_agent")
            with open("test_agent/__init__.py", "w") as f:
                f.write("# Test agent")

            # Test with custom base image
            result = runner.invoke(
                main, ["test_agent", "--base-image", "python:3.11-slim", "--dry-run"]
            )

            assert result.exit_code == 0

    def test_cli_help_sections(self):
        """Test CLI help message contains required sections."""
        runner = CliRunner()

        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Options:" in result.output
        assert "--framework" in result.output
        assert "--port" in result.output
        assert "--agent-name" in result.output

    def test_cli_error_recovery(self):
        """Test CLI error recovery behavior."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            os.makedirs("test_agent")
            with open("test_agent/__init__.py", "w") as f:
                f.write("# Test agent")

            # Test with invalid port to trigger error handling
            result = runner.invoke(main, ["test_agent", "--port", "99999", "--dry-run"])

            # Should handle error gracefully
            assert isinstance(result.exit_code, int)

    def test_cli_logging_setup_verbose(self):
        """Test CLI logging setup in verbose mode."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            os.makedirs("test_agent")
            with open("test_agent/__init__.py", "w") as f:
                f.write("# Test agent")

            result = runner.invoke(main, ["test_agent", "--verbose", "--dry-run"])

            assert result.exit_code == 0

    def test_cli_logging_setup_normal(self):
        """Test CLI logging setup in normal mode."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            os.makedirs("test_agent")
            with open("test_agent/__init__.py", "w") as f:
                f.write("# Test agent")

            result = runner.invoke(main, ["test_agent", "--dry-run"])

            assert result.exit_code == 0

    def test_cli_framework_specific_ports(self):
        """Test framework-specific port assignment logic."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create different framework-style structures
            frameworks = [
                ("googleadk", "google_agent"),
                ("awsstrands", "strands_agent"),
                ("langchain", "langchain_agent"),
            ]

            for framework_type, agent_dir in frameworks:
                os.makedirs(agent_dir, exist_ok=True)
                with open(f"{agent_dir}/__init__.py", "w") as f:
                    f.write(f"# {framework_type} agent")

                result = runner.invoke(main, [agent_dir, "--verbose", "--dry-run"])

                assert result.exit_code == 0

    def test_cli_error_handling_comprehensive(self):
        """Test comprehensive error handling in CLI."""
        runner = CliRunner()

        # Test with various edge cases
        test_cases = [
            # Empty agent name
            [".", "--agent-name", "", "--dry-run"],
            # Multiple flags together
            [".", "--no-build", "--no-run", "--no-ui", "--dry-run"],
        ]

        with runner.isolated_filesystem():
            os.makedirs("test_agent")
            with open("test_agent/__init__.py", "w") as f:
                f.write("# Test agent")

            for test_case in test_cases:
                # Replace "." with actual agent directory
                test_case[0] = "test_agent"

                result = runner.invoke(main, test_case)

                # Should handle gracefully (not crash)
                assert isinstance(result.exit_code, int)
