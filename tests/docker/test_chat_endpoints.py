"""Tests for chat endpoint generation in Docker containers."""

import pytest
import re

from any_agent.docker.docker_generator import UnifiedDockerfileGenerator
from any_agent.adapters.base import AgentMetadata


class TestChatEndpointsGeneration:
    """Test suite for chat endpoint generation in Docker containers."""

    @pytest.fixture
    def generator(self):
        """Create UnifiedDockerfileGenerator instance."""
        return UnifiedDockerfileGenerator()

    @pytest.fixture
    def mock_metadata(self):
        """Create mock agent metadata."""
        return AgentMetadata(
            framework="google_adk", name="Test Agent", local_dependencies=["google-adk"]
        )

    def test_generate_chat_endpoints_generic_includes_cleanup(self, generator):
        """Test that generic (FastAPI) chat endpoints include cleanup endpoint."""
        endpoints_code = generator._generate_chat_endpoints("generic")

        # Should include all three endpoints
        assert "create_chat_session_endpoint" in endpoints_code
        assert "send_chat_message_endpoint" in endpoints_code
        assert "cleanup_chat_session_endpoint" in endpoints_code

        # Should register all three routes
        assert (
            'app.post("/chat/create-session")(create_chat_session_endpoint)'
            in endpoints_code
        )
        assert (
            'app.post("/chat/send-message")(send_chat_message_endpoint)'
            in endpoints_code
        )
        assert (
            'app.post("/chat/cleanup-session")(cleanup_chat_session_endpoint)'
            in endpoints_code
        )

    def test_generate_chat_endpoints_starlette_includes_cleanup(self, generator):
        """Test that Starlette (ADK/Strands) chat endpoints include cleanup and cancel endpoints."""
        endpoints_code = generator._generate_chat_endpoints("adk")

        # Should include all four endpoints
        assert "create_chat_session_endpoint" in endpoints_code
        assert "send_chat_message_endpoint" in endpoints_code
        assert "cleanup_chat_session_endpoint" in endpoints_code
        assert "cancel_chat_task_endpoint" in endpoints_code

        # Should register all four routes using Route and app.routes.extend
        assert 'Route("/chat/create-session", create_chat_session_endpoint' in endpoints_code
        assert 'Route("/chat/send-message", send_chat_message_endpoint' in endpoints_code
        assert 'Route("/chat/cleanup-session", cleanup_chat_session_endpoint' in endpoints_code
        assert 'Route("/chat/cancel-task", cancel_chat_task_endpoint' in endpoints_code
        assert 'app.routes.extend([chat_create_route, chat_send_route, chat_cleanup_route, chat_cancel_route])' in endpoints_code

    def test_cleanup_endpoint_validates_session_id(self, generator):
        """Test that cleanup endpoint validates session_id parameter."""
        endpoints_code = generator._generate_chat_endpoints("generic")

        # Should include session_id validation
        assert "session_id = request_body.get('session_id')" in endpoints_code
        assert "if not session_id:" in endpoints_code
        assert '"session_id required"' in endpoints_code

    def test_cleanup_endpoint_calls_chat_handler(self, generator):
        """Test that cleanup endpoint calls chat_handler.cleanup_session."""
        endpoints_code = generator._generate_chat_endpoints("generic")

        # Should call cleanup_session method
        assert "chat_handler.cleanup_session(session_id)" in endpoints_code

    def test_cleanup_endpoint_error_handling(self, generator):
        """Test that cleanup endpoint has proper error handling."""
        endpoints_code = generator._generate_chat_endpoints("generic")

        # Should have try/except around cleanup call
        assert "try:" in endpoints_code
        assert "except Exception as error:" in endpoints_code
        assert "Failed to cleanup session" in endpoints_code

    def test_adk_entrypoint_includes_chat_endpoints(self, generator, mock_metadata):
        """Test that ADK entrypoint generation includes chat endpoints."""
        from pathlib import Path

        agent_path = Path("/test/agent")
        entrypoint_code = generator._generate_adk_entrypoint(
            agent_path, mock_metadata, add_ui=True
        )

        # Should include actual chat endpoints implementation
        assert "cleanup_chat_session_endpoint" in entrypoint_code
        assert 'Route("/chat/cleanup-session", cleanup_chat_session_endpoint' in entrypoint_code

    def test_strands_entrypoint_includes_chat_endpoints(self, generator, mock_metadata):
        """Test that Strands entrypoint generation includes chat endpoints."""
        from pathlib import Path

        # Create Strands metadata
        strands_metadata = AgentMetadata(
            framework="aws_strands",
            name="Test Strands Agent",
            local_dependencies=["strands-agents"],
        )

        agent_path = Path("/test/agent")
        entrypoint_code = generator._generate_strands_entrypoint(
            agent_path, strands_metadata, add_ui=True
        )

        # Should include actual chat endpoints implementation
        assert "cleanup_chat_session_endpoint" in entrypoint_code
        assert 'Route("/chat/cleanup-session", cleanup_chat_session_endpoint' in entrypoint_code

    def test_chat_handler_import_in_endpoints(self, generator):
        """Test that chat endpoints properly import A2AChatHandler."""
        endpoints_code = generator._generate_chat_endpoints("generic")

        # Should import chat handler
        assert "from any_agent.api.chat_handler import A2AChatHandler" in endpoints_code

        # Should create chat handler instance
        assert "chat_handler = A2AChatHandler(timeout=300)" in endpoints_code

    def test_json_response_import_in_endpoints(self, generator):
        """Test that endpoints import JSONResponse properly."""
        generic_code = generator._generate_chat_endpoints("generic")
        starlette_code = generator._generate_chat_endpoints("adk")

        # Generic should reference JSONResponse (imported elsewhere)
        assert "JSONResponse" in generic_code

        # Starlette should reference JSONResponse (imported elsewhere)
        assert "JSONResponse" in starlette_code

    def test_endpoints_logging(self, generator):
        """Test that endpoints include proper logging."""
        endpoints_code = generator._generate_chat_endpoints("generic")

        # Should log success
        assert "Chat endpoints added successfully" in endpoints_code

        # Should log errors
        assert "Failed to cleanup session" in endpoints_code

    def test_endpoints_exception_handling(self, generator):
        """Test comprehensive exception handling in endpoints."""
        endpoints_code = generator._generate_chat_endpoints("generic")

        # Should handle import errors
        assert "ImportError as import_error" in endpoints_code
        assert "Failed to import chat handler" in endpoints_code

        # Should handle general setup errors
        assert "Exception as chat_setup_error" in endpoints_code
        assert "Failed to setup chat endpoints" in endpoints_code

    def test_starlette_request_parsing(self, generator):
        """Test that Starlette endpoints parse requests correctly."""
        starlette_code = generator._generate_chat_endpoints("adk")

        # Should parse JSON from request
        assert "request_body = await request.json()" in starlette_code

        # Should handle JSON parsing errors
        assert "Failed to parse request" in starlette_code
        assert "Invalid JSON" in starlette_code

    def test_session_cleanup_response_format(self, generator):
        """Test that cleanup endpoint returns proper response format."""
        endpoints_code = generator._generate_chat_endpoints("generic")

        # Should return result from chat_handler.cleanup_session
        assert "result = chat_handler.cleanup_session(session_id)" in endpoints_code
        assert "return JSONResponse(result)" in endpoints_code

    def test_all_frameworks_support_cleanup(self, generator):
        """Test that all supported frameworks include cleanup endpoint."""
        frameworks = ["generic", "adk", "strands"]

        for framework in frameworks:
            endpoints_code = generator._generate_chat_endpoints(framework)

            # Each should include cleanup endpoint
            assert "cleanup_chat_session_endpoint" in endpoints_code, (
                f"Framework {framework} missing cleanup endpoint"
            )

    def test_endpoint_path_consistency(self, generator):
        """Test that endpoint paths are consistent across frameworks."""
        generic_code = generator._generate_chat_endpoints("generic")
        starlette_code = generator._generate_chat_endpoints("adk")

        # All should use same endpoint paths
        paths = ["/chat/create-session", "/chat/send-message", "/chat/cleanup-session"]

        for path in paths:
            assert path in generic_code, f"Generic missing path {path}"
            assert path in starlette_code, f"Starlette missing path {path}"

    def test_http_methods_consistency(self, generator):
        """Test that all chat endpoints use POST method."""
        generic_code = generator._generate_chat_endpoints("generic")
        starlette_code = generator._generate_chat_endpoints("adk")

        # Generic uses app.post()
        post_calls = re.findall(r'app\.post\("([^"]+)"\)', generic_code)
        expected_paths = [
            "/chat/create-session",
            "/chat/send-message",
            "/chat/cleanup-session",
            "/chat/cancel-task",
        ]

        assert set(post_calls) == set(expected_paths)

        # Starlette should specify POST methods
        assert 'methods=["POST"]' in starlette_code

    def test_timeout_configuration(self, generator):
        """Test that chat handler timeout is configurable."""
        endpoints_code = generator._generate_chat_endpoints("generic")

        # Should create handler with timeout
        assert "A2AChatHandler(timeout=300)" in endpoints_code

    def test_agent_url_default_handling(self, generator):
        """Test that agent_url defaults to current container."""
        endpoints_code = generator._generate_chat_endpoints("generic")

        # Should use url_builder for agent_url handling
        assert "url_builder.agent_url_with_fallback(request_body.get('agent_url'))" in endpoints_code


class TestChatEndpointIntegration:
    """Integration tests for chat endpoints in complete Docker generation."""

    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return UnifiedDockerfileGenerator()

    def test_complete_adk_entrypoint_with_cleanup(self, generator):
        """Test complete ADK entrypoint includes cleanup functionality."""
        from pathlib import Path

        metadata = AgentMetadata(
            framework="google_adk",
            name="Test ADK Agent",
            local_dependencies=["google-adk"],
        )

        entrypoint_code = generator._generate_adk_entrypoint(
            Path("/test"), metadata, add_ui=True
        )

        # Should include imports needed for cleanup
        assert (
            "from any_agent.api.chat_handler import A2AChatHandler" in entrypoint_code
        )
        assert "from starlette.responses import JSONResponse" in entrypoint_code

        # Should include all chat routes using app.mount
        assert 'Route("/chat/cleanup-session", cleanup_chat_session_endpoint' in entrypoint_code

    def test_dockerfile_generation_preserves_cleanup(self, generator):
        """Test that complete Dockerfile generation preserves cleanup endpoints."""
        from pathlib import Path

        metadata = AgentMetadata(
            framework="google_adk", name="Test Agent", local_dependencies=["google-adk"]
        )

        dockerfile_content = generator.generate_dockerfile(Path("/test"), metadata)

        # Dockerfile should preserve the structure that includes cleanup endpoints
        assert "COPY" in dockerfile_content  # Should copy agent code
        assert "CMD" in dockerfile_content  # Should have run command


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
