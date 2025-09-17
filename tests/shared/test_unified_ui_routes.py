"""Tests for unified UI route generation."""

import pytest

from any_agent.shared.unified_ui_routes import (
    UIConfig,
    StarletteUIRouteBuilder,
    FastAPIUIRouteBuilder,
    UnifiedUIRouteGenerator,
    unified_ui_generator
)


class TestUIConfig:
    """Test UIConfig dataclass."""

    def test_ui_config_creation(self):
        """Test basic UIConfig creation."""
        config = UIConfig(
            add_ui=True,
            framework="adk",
            deployment_type="docker"
        )
        assert config.add_ui is True
        assert config.framework == "adk"
        assert config.deployment_type == "docker"
        assert config.port is None
        assert config.static_dir == "/app/static"


class TestStarletteUIRouteBuilder:
    """Test Starlette UI route builder."""

    def test_disabled_ui_returns_empty(self):
        """Test that disabled UI returns empty string."""
        config = UIConfig(add_ui=False, framework="adk", deployment_type="docker")
        builder = StarletteUIRouteBuilder(config)
        result = builder.generate_routes()
        assert result == ""

    def test_docker_starlette_routes(self):
        """Test Docker Starlette route generation."""
        config = UIConfig(add_ui=True, framework="adk", deployment_type="docker")
        builder = StarletteUIRouteBuilder(config)
        result = builder.generate_routes()

        # Check key components
        assert "from starlette.responses import HTMLResponse, FileResponse" in result
        assert "from starlette.staticfiles import StaticFiles" in result
        assert "from starlette.routing import Route, Mount" in result
        assert "/app/static" in result
        assert "async def serve_spa(request):" in result
        assert 'Route("/", serve_spa, methods=["GET"])' in result

    def test_localhost_starlette_routes(self):
        """Test localhost Starlette route generation."""
        config = UIConfig(
            add_ui=True,
            framework="strands",
            deployment_type="localhost",
            port=8080,
            agent_name="test_agent"
        )
        builder = StarletteUIRouteBuilder(config)
        result = builder.generate_routes()

        # Check localhost-specific components
        assert "Path(__file__).parent / \"static\"" in result
        assert "test_agent" in result
        assert "localhost_mode" in result
        assert "strands" in result

    def test_static_dir_override(self):
        """Test custom static directory."""
        config = UIConfig(
            add_ui=True,
            framework="adk",
            deployment_type="localhost",
            localhost_static_dir="/custom/static"
        )
        builder = StarletteUIRouteBuilder(config)
        assert builder._get_static_dir() == "/custom/static"


class TestFastAPIUIRouteBuilder:
    """Test FastAPI UI route builder."""

    def test_disabled_ui_returns_empty(self):
        """Test that disabled UI returns empty string."""
        config = UIConfig(add_ui=False, framework="generic", deployment_type="docker")
        builder = FastAPIUIRouteBuilder(config)
        result = builder.generate_routes()
        assert result == ""

    def test_fastapi_routes(self):
        """Test FastAPI route generation."""
        config = UIConfig(add_ui=True, framework="generic", deployment_type="docker")
        builder = FastAPIUIRouteBuilder(config)
        result = builder.generate_routes()

        # Check key components
        assert "from fastapi.responses import HTMLResponse, FileResponse" in result
        assert "from fastapi.staticfiles import StaticFiles" in result
        assert "app.mount" in result
        assert "@app.get" in result
        assert "async def serve_spa():" in result
        assert "/app/static" in result


class TestUnifiedUIRouteGenerator:
    """Test unified UI route generator."""

    def test_disabled_ui_returns_empty(self):
        """Test that disabled UI returns empty string."""
        config = UIConfig(add_ui=False, framework="generic", deployment_type="docker")
        generator = UnifiedUIRouteGenerator()
        result = generator.generate_ui_routes(config)
        assert result == ""

    def test_adk_uses_starlette(self):
        """Test that ADK framework uses Starlette routes."""
        config = UIConfig(add_ui=True, framework="adk", deployment_type="docker")
        generator = UnifiedUIRouteGenerator()
        result = generator.generate_ui_routes(config)

        # Should use Starlette patterns
        assert "from starlette.responses" in result
        assert "Route(" in result

    def test_strands_uses_starlette(self):
        """Test that Strands framework uses Starlette routes."""
        config = UIConfig(add_ui=True, framework="strands", deployment_type="docker")
        generator = UnifiedUIRouteGenerator()
        result = generator.generate_ui_routes(config)

        # Should use Starlette patterns
        assert "from starlette.responses" in result
        assert "Route(" in result

    def test_generic_uses_fastapi_in_docker(self):
        """Test that generic framework uses FastAPI in Docker."""
        config = UIConfig(add_ui=True, framework="generic", deployment_type="docker")
        generator = UnifiedUIRouteGenerator()
        result = generator.generate_ui_routes(config)

        # Should use FastAPI patterns
        assert "from fastapi.responses" in result
        assert "@app.get" in result

    def test_localhost_always_uses_starlette(self):
        """Test that localhost deployment always uses Starlette."""
        config = UIConfig(add_ui=True, framework="generic", deployment_type="localhost")
        generator = UnifiedUIRouteGenerator()
        result = generator.generate_ui_routes(config)

        # Should use Starlette even for generic framework
        assert "from starlette" in result

    def test_legacy_localhost_ui_routes(self):
        """Test legacy localhost UI routes method."""
        generator = UnifiedUIRouteGenerator()
        result = generator.generate_localhost_ui_routes(
            add_ui=True, port=8080, agent_name="test_agent"
        )

        assert "test_agent" in result
        assert "localhost_mode" in result

    def test_legacy_docker_ui_routes(self):
        """Test legacy Docker UI routes method."""
        generator = UnifiedUIRouteGenerator()
        result = generator.generate_docker_ui_routes(add_ui=True, framework="adk")

        assert "from starlette" in result  # ADK uses Starlette
        assert "/app/static" in result

    def test_singleton_instance(self):
        """Test that singleton instance exists and works."""
        result = unified_ui_generator.generate_docker_ui_routes(
            add_ui=True, framework="generic"
        )
        assert "from fastapi" in result  # Generic uses FastAPI in Docker