"""Unified UI route creation for consistent patterns across frameworks.

Eliminates duplication between FastAPI and Starlette UI route generation
by providing a standardized interface that abstracts framework differences.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class UIConfig:
    """Configuration for UI route generation."""

    add_ui: bool
    framework: str  # "adk", "strands", "generic"
    deployment_type: str  # "docker", "localhost"
    port: Optional[int] = None
    agent_name: Optional[str] = None
    static_dir: str = "/app/static"  # Docker default
    localhost_static_dir: Optional[str] = None


class UIRouteBuilder(ABC):
    """Abstract base for UI route builders."""

    def __init__(self, config: UIConfig):
        """Initialize with UI configuration."""
        self.config = config

    @abstractmethod
    def generate_routes(self) -> str:
        """Generate UI routes code for specific framework style.

        Returns:
            Generated UI routes code as string
        """
        pass

    def _get_static_dir(self) -> str:
        """Get appropriate static directory based on deployment type."""
        if (
            self.config.deployment_type == "localhost"
            and self.config.localhost_static_dir
        ):
            return self.config.localhost_static_dir
        return self.config.static_dir



class StarletteUIRouteBuilder(UIRouteBuilder):
    """Starlette-style UI route builder."""

    def generate_routes(self) -> str:
        """Generate Starlette-style UI routes."""
        if not self.config.add_ui:
            return ""

        static_dir = self._get_static_dir()

        if self.config.deployment_type == "localhost":
            return self._generate_localhost_starlette_routes(static_dir)
        else:
            return self._generate_docker_starlette_routes(static_dir)

    def _generate_docker_starlette_routes(self, static_dir: str) -> str:
        """Generate Docker-specific Starlette routes."""
        return f"""
    # Add UI routes (Starlette style)
    from starlette.responses import HTMLResponse, FileResponse
    from starlette.staticfiles import StaticFiles
    from starlette.routing import Route, Mount
    import os

    # Mount static files
    if os.path.exists("{static_dir}"):
        static_mount = Mount("/static", StaticFiles(directory="{static_dir}"), name="static")
        app.routes.append(static_mount)
        if os.path.exists("{static_dir}/assets"):
            assets_mount = Mount("/assets", StaticFiles(directory="{static_dir}/assets"), name="assets")
            app.routes.append(assets_mount)

    async def serve_spa(request):
        try:
            index_path = "{static_dir}/index.html"
            if os.path.exists(index_path):
                return FileResponse(index_path)
            else:
                return HTMLResponse("<h1>UI Not Available</h1><p>React SPA could not be loaded for {self.config.agent_name or "agent"}.</p>", status_code=503)
        except Exception:
            return HTMLResponse("<h1>Error</h1><p>Failed to serve UI.</p>", status_code=500)

    ui_routes = [
        Route("/", serve_spa, methods=["GET"]),
        Route("/describe", serve_spa, methods=["GET"])
    ]
    app.routes.extend(ui_routes)
"""

    def _generate_localhost_starlette_routes(self, static_dir: str) -> str:
        """Generate localhost-specific Starlette routes."""
        agent_name = self.config.agent_name or "agent"

        return f"""
    # Add static file serving if UI enabled (localhost mode)
    if True:
        from starlette.staticfiles import StaticFiles
        from starlette.responses import FileResponse
        from starlette.routing import Route
        from pathlib import Path

        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")
            logger.info(f"📁 Mounted static files from {{static_dir}}")

            # Add route to serve index.html at root
            async def serve_ui(request):
                index_file = static_dir / "index.html"
                if index_file.exists():
                    return FileResponse(index_file)
                else:
                    from starlette.responses import JSONResponse
                    return JSONResponse({{
                        "agent": "{agent_name}",
                        "framework": "{self.config.framework}",
                        "localhost_mode": True,
                        "status": "ui_enabled",
                        "error": "UI files not found"
                    }})

            # Add UI route at root
            ui_route = Route("/", serve_ui, methods=["GET"])
            app.routes.append(ui_route)
        else:
            logger.warning("📁 Static directory not found - UI files not served")
"""


class FastAPIUIRouteBuilder(UIRouteBuilder):
    """FastAPI-style UI route builder."""

    def generate_routes(self) -> str:
        """Generate FastAPI-style UI routes."""
        if not self.config.add_ui:
            return ""

        static_dir = self._get_static_dir()

        return f"""
    # Add UI routes (FastAPI style)
    from fastapi.responses import HTMLResponse, FileResponse
    from fastapi.staticfiles import StaticFiles
    import os

    # Mount static files
    if os.path.exists("{static_dir}"):
        app.mount("/static", StaticFiles(directory="{static_dir}"), name="static")
        if os.path.exists("{static_dir}/assets"):
            app.mount("/assets", StaticFiles(directory="{static_dir}/assets"), name="assets")

    @app.get("/")
    @app.get("/describe")
    async def serve_spa():
        try:
            index_path = "{static_dir}/index.html"
            if os.path.exists(index_path):
                return FileResponse(index_path)
            else:
                return HTMLResponse("<h1>UI Not Available</h1><p>React SPA could not be loaded for {self.config.agent_name or "agent"}.</p>", status_code=503)
        except Exception:
            return HTMLResponse("<h1>Error</h1><p>Failed to serve UI.</p>", status_code=500)
"""


class UnifiedUIRouteGenerator:
    """Unified generator that selects appropriate builder based on configuration."""

    def generate_ui_routes(self, config: UIConfig) -> str:
        """Generate UI routes using appropriate builder.

        Args:
            config: UI configuration

        Returns:
            Generated UI routes code
        """
        if not config.add_ui:
            return ""

        # Select builder based on framework and requirements
        builder: UIRouteBuilder
        if (
            config.framework in ["adk", "strands"]
            or config.deployment_type == "localhost"
        ):
            # Use Starlette for A2A compatibility and localhost
            builder = StarletteUIRouteBuilder(config)
        else:
            # Use FastAPI for generic frameworks
            builder = FastAPIUIRouteBuilder(config)

        return builder.generate_routes()

    def generate_localhost_ui_routes(
        self, add_ui: bool, port: int, agent_name: str, framework: str = "generic"
    ) -> str:
        """Generate localhost-specific UI routes (legacy compatibility).

        Args:
            add_ui: Whether to add UI routes
            port: Agent port
            agent_name: Name of agent
            framework: Framework type

        Returns:
            Generated UI routes code
        """
        config = UIConfig(
            add_ui=add_ui,
            framework=framework,
            deployment_type="localhost",
            port=port,
            agent_name=agent_name,
        )
        return self.generate_ui_routes(config)

    def generate_docker_ui_routes(
        self, add_ui: bool, framework: str = "generic"
    ) -> str:
        """Generate Docker-specific UI routes (legacy compatibility).

        Args:
            add_ui: Whether to add UI routes
            framework: Framework type

        Returns:
            Generated UI routes code
        """
        config = UIConfig(add_ui=add_ui, framework=framework, deployment_type="docker")
        return self.generate_ui_routes(config)


# Singleton instance for backward compatibility
unified_ui_generator = UnifiedUIRouteGenerator()
