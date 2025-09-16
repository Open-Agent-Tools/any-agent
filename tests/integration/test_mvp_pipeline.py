"""Test the MVP pipeline with the existing adk_test_agent."""

import pytest
import socket
from pathlib import Path
from unittest.mock import patch, MagicMock

from any_agent.adapters.google_adk_adapter import GoogleADKAdapter
from any_agent.core.docker_orchestrator import AgentOrchestrator


class TestMVPPipeline:
    """Test the MVP pipeline functionality."""

    def test_adk_adapter_detects_test_agent(self):
        """Test that ADK adapter can detect the adk_test_agent."""
        adapter = GoogleADKAdapter()

        # Path to our test agent
        test_agent_path = (
            Path(__file__).parent.parent.parent / "examples" / "Google_ADK" / "Testing_Tessie"
        )

        # Should detect the agent
        assert adapter.detect(test_agent_path)

    def test_adk_adapter_validates_test_agent(self):
        """Test that ADK adapter can validate the adk_test_agent."""
        adapter = GoogleADKAdapter()

        test_agent_path = (
            Path(__file__).parent.parent.parent / "examples" / "Google_ADK" / "Testing_Tessie"
        )

        # Should validate successfully
        validation = adapter.validate(test_agent_path)
        assert validation.is_valid

    def test_adk_adapter_extracts_metadata(self):
        """Test metadata extraction from adk_test_agent."""
        adapter = GoogleADKAdapter()

        test_agent_path = (
            Path(__file__).parent.parent.parent / "examples" / "Google_ADK" / "Testing_Tessie"
        )

        metadata = adapter.extract_metadata(test_agent_path)

        assert metadata.name == "Testing_Tessie"
        assert metadata.framework == "google_adk"
        assert metadata.entry_point == "root_agent"

    def test_orchestrator_detects_framework(self):
        """Test that orchestrator can detect framework for test agent."""
        orchestrator = AgentOrchestrator()

        test_agent_path = (
            Path(__file__).parent.parent.parent / "examples" / "Google_ADK" / "Testing_Tessie"
        )

        adapter = orchestrator.detect_framework(test_agent_path)

        assert adapter is not None
        assert adapter.framework_name == "google_adk"

    @patch("subprocess.run")
    @patch("requests.get")
    @patch("requests.post")
    def test_full_pipeline_dry_run(self, mock_post, mock_get, mock_subprocess):
        """Test the full pipeline with mocked Docker operations."""
        # Mock subprocess calls (Docker commands)
        mock_subprocess.return_value = MagicMock(
            stdout="container_id_12345\n", stderr="", returncode=0
        )

        # Mock health check
        health_response = MagicMock()
        health_response.status_code = 200
        health_response.json.return_value = {
            "status": "healthy",
            "agent_name": "test",
            "framework": "google_adk",
        }

        # Mock describe endpoint
        describe_response = MagicMock()
        describe_response.status_code = 200
        describe_response.json.return_value = {
            "name": "test_agent",
            "framework": "google_adk",
        }

        # Mock chat endpoint
        chat_response = MagicMock()
        chat_response.status_code = 200
        chat_response.json.return_value = {"response": "Hello! I am a test agent."}

        mock_get.side_effect = [health_response, describe_response]
        mock_post.return_value = chat_response

        orchestrator = AgentOrchestrator()
        test_agent_path = (
            Path(__file__).parent.parent.parent / "examples" / "Google_ADK" / "Testing_Tessie"
        )

        # Run pipeline with mocked operations
        results = orchestrator.run_full_pipeline(
            agent_path=str(test_agent_path),
            output_dir="/tmp/test_output",
            port=58000,  # Use high port unlikely to be in use
        )

        # Should succeed
        assert results["success"]
        assert "port_check" in results["steps"]
        assert "detection" in results["steps"]
        assert "validation" in results["steps"]
        assert "metadata" in results["steps"]
        assert "docker_build" in results["steps"]
        assert "container_start" in results["steps"]
        assert "health_check" in results["steps"]
        assert "e2e_test" in results["steps"]

    def test_invalid_agent_path(self):
        """Test handling of invalid agent path."""
        orchestrator = AgentOrchestrator()

        # Non-existent path
        results = orchestrator.run_full_pipeline("/non/existent/path", port=58001)

        assert not results["success"]
        # Should fail early, but might have port_check step
        if "port_check" in results["steps"]:
            # If port check happened, should pass and then fail on detection
            assert "detection" in results["steps"]
            assert "error" in results["steps"]["detection"]
        else:
            # Should have some error
            assert "error" in results

    def test_port_conflict_stops_pipeline(self):
        """Test that a port conflict stops the pipeline early."""
        orchestrator = AgentOrchestrator()

        # Bind to a port to make it unavailable
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("localhost", 0))
            busy_port = sock.getsockname()[1]

            test_agent_path = (
                Path(__file__).parent.parent.parent / "examples" / "Google_ADK" / "Testing_Tessie"
            )

            # Try to run pipeline on busy port
            results = orchestrator.run_full_pipeline(
                agent_path=str(test_agent_path), port=busy_port
            )

            # Should fail early at port check
            assert not results["success"]
            assert "port_check" in results["steps"]
            assert "error" in results["steps"]["port_check"]
            assert (
                f"Port {busy_port} is not available"
                in results["steps"]["port_check"]["error"]
            )

            # Should suggest an alternative port
            if "suggested_port" in results["steps"]["port_check"]:
                suggested = results["steps"]["port_check"]["suggested_port"]
                if suggested:
                    # Suggested port should be available
                    test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    try:
                        test_sock.bind(("localhost", suggested))
                        test_sock.close()
                    except OSError:
                        pytest.fail(
                            f"Suggested port {suggested} is not actually available"
                        )
