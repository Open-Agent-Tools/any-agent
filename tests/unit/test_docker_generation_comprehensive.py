"""Comprehensive Docker generation test suite for container build coverage."""

from unittest.mock import patch

from any_agent.docker.docker_generator import UnifiedDockerfileGenerator
from any_agent.adapters.base import AgentMetadata


class TestUnifiedDockerfileGeneratorComprehensive:
    """Comprehensive tests for Unified Dockerfile Generator."""

    def test_init_base_configuration(self):
        """Test UnifiedDockerfileGenerator initialization."""
        generator = UnifiedDockerfileGenerator()

        assert generator.base_image == "python:3.11-slim"
        assert "google_adk" in generator.framework_configs
        assert "aws_strands" in generator.framework_configs
        assert "langchain" in generator.framework_configs
        assert "langgraph" in generator.framework_configs
        assert "crewai" in generator.framework_configs

    def test_get_framework_config_google_adk(self):
        """Test getting Google ADK framework configuration."""
        generator = UnifiedDockerfileGenerator()

        config = generator.get_framework_config("google_adk")

        assert config["default_port"] == 8035
        assert "GOOGLE_MODEL" in config["env_vars"]
        assert "GOOGLE_API_KEY" in config["env_vars"]
        assert "google-adk[a2a]" in config["dependencies"]
        assert config["entrypoint_script"] == "_adk_entrypoint.py"
        assert config["server_type"] == "google_adk_a2a"

    def test_get_framework_config_aws_strands(self):
        """Test getting AWS Strands framework configuration."""
        generator = UnifiedDockerfileGenerator()

        config = generator.get_framework_config("aws_strands")

        assert config["default_port"] == 8045
        assert "ANTHROPIC_API_KEY" in config["env_vars"]
        assert "strands-agents[a2a]" in config["dependencies"]
        assert "fastapi" in config["dependencies"]
        assert config["entrypoint_script"] == "_strands_entrypoint.py"
        assert config["server_type"] == "strands_a2a"

    def test_get_framework_config_unknown_framework(self):
        """Test getting configuration for unknown framework."""
        generator = UnifiedDockerfileGenerator()

        with patch("any_agent.docker.docker_generator.logger") as mock_logger:
            config = generator.get_framework_config("unknown_framework")

            assert config["default_port"] == 8085
            assert config["server_type"] == "generic_a2a"
            assert "uvicorn[standard]" in config["dependencies"]
            assert "a2a-sdk>=0.1.0" in config["dependencies"]
            mock_logger.warning.assert_called_once()

    def test_generate_dockerfile_google_adk(self, tmp_path):
        """Test Dockerfile generation for Google ADK."""
        generator = UnifiedDockerfileGenerator()

        # Create test metadata
        metadata = AgentMetadata(
            name="test-adk-agent", framework="google_adk", description="Test ADK agent"
        )

        agent_path = tmp_path / "agent"
        agent_path.mkdir()

        dockerfile_content = generator.generate_dockerfile(agent_path, metadata)

        # Verify basic structure
        assert "FROM python:3.11-slim" in dockerfile_content
        assert "test-adk-agent" in dockerfile_content
        assert "Google Adk Agent" in dockerfile_content
        assert "WORKDIR /app" in dockerfile_content

        # Verify framework-specific configuration
        assert "ENV AGENT_FRAMEWORK=google_adk" in dockerfile_content
        assert "ENV GOOGLE_MODEL=" in dockerfile_content
        assert "ENV GOOGLE_API_KEY=" in dockerfile_content
        assert "ENV AGENT_PORT=8035" in dockerfile_content
        assert "COPY _adk_entrypoint.py" in dockerfile_content

        # Verify build steps
        assert "uv pip install" in dockerfile_content
        assert "COPY requirements.txt" in dockerfile_content
        assert "COPY . ." in dockerfile_content
        assert "HEALTHCHECK" in dockerfile_content
        assert "uvicorn" in dockerfile_content

    def test_generate_dockerfile_aws_strands(self, tmp_path):
        """Test Dockerfile generation for AWS Strands."""
        generator = UnifiedDockerfileGenerator()

        metadata = AgentMetadata(
            name="test-strands-agent",
            framework="aws_strands",
            description="Test Strands agent",
        )

        agent_path = tmp_path / "agent"
        agent_path.mkdir()

        dockerfile_content = generator.generate_dockerfile(agent_path, metadata)

        # Verify Strands-specific configuration
        assert "test-strands-agent" in dockerfile_content
        assert "Aws Strands Agent" in dockerfile_content
        assert "ENV AGENT_FRAMEWORK=aws_strands" in dockerfile_content
        assert "ENV ANTHROPIC_API_KEY=" in dockerfile_content
        assert "ENV AGENT_PORT=8045" in dockerfile_content
        assert "COPY _strands_entrypoint.py" in dockerfile_content

    def test_generate_dockerfile_content_structure(self, tmp_path):
        """Test comprehensive Dockerfile content structure."""
        generator = UnifiedDockerfileGenerator()

        metadata = AgentMetadata(
            name="structure-test", framework="google_adk", description="Test structure"
        )

        agent_path = tmp_path / "agent"
        agent_path.mkdir()

        dockerfile_content = generator.generate_dockerfile(agent_path, metadata)
        lines = dockerfile_content.split("\n")

        # Check for essential sections
        base_image_found = any("FROM python:" in line for line in lines)
        workdir_found = any("WORKDIR /app" in line for line in lines)
        pythonpath_found = any("ENV PYTHONPATH=/app" in line for line in lines)
        system_deps_found = any("apt-get update" in line for line in lines)
        uv_install_found = any(
            "pip install --no-cache-dir uv" in line for line in lines
        )
        requirements_found = any("COPY requirements.txt" in line for line in lines)
        copy_all_found = any("COPY . ." in line for line in lines)
        expose_found = any("EXPOSE $AGENT_PORT" in line for line in lines)
        healthcheck_found = any("HEALTHCHECK" in line for line in lines)
        cmd_found = any("CMD" in line for line in lines)

        assert base_image_found, "Missing base image"
        assert workdir_found, "Missing workdir"
        assert pythonpath_found, "Missing PYTHONPATH"
        assert system_deps_found, "Missing system dependencies"
        assert uv_install_found, "Missing uv installation"
        assert requirements_found, "Missing requirements copy"
        assert copy_all_found, "Missing source copy"
        assert expose_found, "Missing port expose"
        assert healthcheck_found, "Missing healthcheck"
        assert cmd_found, "Missing CMD instruction"

    def test_generate_entrypoint_google_adk(self, tmp_path):
        """Test entrypoint generation for Google ADK."""
        generator = UnifiedDockerfileGenerator()

        metadata = AgentMetadata(
            name="adk-entrypoint-test",
            framework="google_adk",
            description="ADK entrypoint test",
        )

        agent_path = tmp_path / "agent"
        agent_path.mkdir()

        entrypoint_content = generator.generate_entrypoint(
            agent_path, metadata, add_ui=False
        )

        # Should delegate to _generate_adk_entrypoint
        assert isinstance(entrypoint_content, str)
        assert len(entrypoint_content) > 0

    @patch(
        "any_agent.docker.docker_generator.UnifiedDockerfileGenerator._generate_adk_entrypoint"
    )
    def test_generate_entrypoint_adk_delegation(self, mock_adk_entrypoint, tmp_path):
        """Test that ADK entrypoint generation delegates correctly."""
        generator = UnifiedDockerfileGenerator()
        mock_adk_entrypoint.return_value = "ADK entrypoint content"

        metadata = AgentMetadata(
            name="delegation-test",
            framework="google_adk",
            description="Delegation test",
        )

        agent_path = tmp_path / "agent"
        agent_path.mkdir()

        result = generator.generate_entrypoint(agent_path, metadata, add_ui=True)

        assert result == "ADK entrypoint content"
        mock_adk_entrypoint.assert_called_once_with(agent_path, metadata, True)

    def test_framework_configs_completeness(self):
        """Test that all framework configurations are complete."""
        generator = UnifiedDockerfileGenerator()

        required_keys = [
            "default_port",
            "env_vars",
            "dependencies",
            "entrypoint_script",
            "server_type",
        ]

        for framework, config in generator.framework_configs.items():
            for key in required_keys:
                assert key in config, f"Missing {key} in {framework} config"

            # Validate port is integer
            assert isinstance(config["default_port"], int)

            # Validate dependencies is list
            assert isinstance(config["dependencies"], list)
            assert len(config["dependencies"]) > 0

            # Validate entrypoint script has .py extension
            assert config["entrypoint_script"].endswith(".py")

            # Validate server type is one of expected values
            assert config["server_type"] in [
                "google_adk_a2a",
                "strands_a2a",
                "generic_a2a",
            ]

    def test_port_assignments_unique(self):
        """Test that framework default ports are unique."""
        generator = UnifiedDockerfileGenerator()

        ports = []
        for config in generator.framework_configs.values():
            ports.append(config["default_port"])

        # All ports should be unique
        assert len(ports) == len(set(ports)), (
            "Duplicate ports found in framework configs"
        )

    def test_dependencies_include_a2a_sdk(self):
        """Test that all framework configurations include a2a-sdk."""
        generator = UnifiedDockerfileGenerator()

        for framework, config in generator.framework_configs.items():
            dependencies = config["dependencies"]

            # Should include a2a-sdk
            a2a_sdk_found = any("a2a-sdk" in dep for dep in dependencies)
            assert a2a_sdk_found, f"a2a-sdk not found in {framework} dependencies"

    def test_all_framework_dockerfile_generation(self, tmp_path):
        """Test Dockerfile generation for all supported frameworks."""
        generator = UnifiedDockerfileGenerator()

        frameworks = ["google_adk", "aws_strands", "langchain", "langgraph", "crewai"]

        for framework in frameworks:
            metadata = AgentMetadata(
                name=f"test-{framework}-agent",
                framework=framework,
                description=f"Test {framework} agent",
            )

            agent_path = tmp_path / f"agent_{framework}"
            agent_path.mkdir()

            dockerfile_content = generator.generate_dockerfile(agent_path, metadata)

            # Basic validation for all frameworks
            assert "FROM python:3.11-slim" in dockerfile_content
            assert f"ENV AGENT_FRAMEWORK={framework}" in dockerfile_content
            assert "uv pip install" in dockerfile_content
            assert "HEALTHCHECK" in dockerfile_content
            assert "CMD" in dockerfile_content
