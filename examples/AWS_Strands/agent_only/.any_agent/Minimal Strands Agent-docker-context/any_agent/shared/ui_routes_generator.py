"""Shared UI routes generator for serving React SPA."""

import logging

logger = logging.getLogger(__name__)


class UIRoutesGenerator:
    """Generate UI serving routes for both localhost and docker pipelines."""

    def generate_ui_routes(
        self, add_ui: bool, framework: str = "generic", request_style: str = "starlette"
    ) -> str:
        """Generate UI serving routes if enabled.

        Args:
            add_ui: Whether to add UI routes
            framework: Framework type ("Google_ADK", "AWS_Strands", "generic")
            request_style: "starlette" or "fastapi"

        Returns:
            Generated UI routes code as string
        """
        if not add_ui:
            return ""

        if request_style == "fastapi":
            return self._generate_fastapi_ui_routes()
        else:
            return self._generate_starlette_ui_routes()

    def _generate_fastapi_ui_routes(self) -> str:
        """Generate FastAPI style UI routes."""
        return """
    # Add UI routes
    from fastapi.responses import HTMLResponse, FileResponse
    from fastapi.staticfiles import StaticFiles
    import os
    
    # Mount static files
    if os.path.exists("/app/static"):
        app.mount("/static", StaticFiles(directory="/app/static"), name="static")
        if os.path.exists("/app/static/assets"):
            app.mount("/assets", StaticFiles(directory="/app/static/assets"), name="assets")
    
    @app.get("/")
    @app.get("/describe")
    async def serve_spa():
        try:
            index_path = "/app/static/index.html"
            if os.path.exists(index_path):
                return FileResponse(index_path)
            else:
                return HTMLResponse("<h1>UI Not Available</h1><p>React SPA could not be loaded.</p>", status_code=503)
        except Exception:
            return HTMLResponse("<h1>Error</h1><p>Failed to serve UI.</p>", status_code=503)
"""

    def _generate_starlette_ui_routes(self) -> str:
        """Generate Starlette style UI routes for ADK and Strands."""
        return """
    # Add UI routes
    from starlette.responses import HTMLResponse, FileResponse
    from starlette.staticfiles import StaticFiles
    from starlette.routing import Route, Mount
    import os
    
    # Mount static files
    if os.path.exists("/app/static"):
        static_mount = Mount("/static", StaticFiles(directory="/app/static"), name="static")
        app.routes.append(static_mount)
        if os.path.exists("/app/static/assets"):
            assets_mount = Mount("/assets", StaticFiles(directory="/app/static/assets"), name="assets")
            app.routes.append(assets_mount)
    
    async def serve_spa(request):
        try:
            index_path = "/app/static/index.html"
            if os.path.exists(index_path):
                return FileResponse(index_path)
            else:
                return HTMLResponse("<h1>UI Not Available</h1><p>React SPA could not be loaded.</p>", status_code=503)
        except Exception:
            return HTMLResponse("<h1>Error</h1><p>Failed to serve UI.</p>", status_code=503)
    
    ui_routes = [
        Route("/", serve_spa, methods=["GET"]),
        Route("/describe", serve_spa, methods=["GET"])
    ]
    app.routes.extend(ui_routes)
"""

    def generate_localhost_ui_routes(
        self, add_ui: bool, port: int, agent_name: str
    ) -> str:
        """Generate localhost-specific UI routes with proper path handling."""
        if not add_ui:
            return ""

        return f"""
    # Add static file serving if UI enabled
    if {str(add_ui).title()}:
        from starlette.staticfiles import StaticFiles
        from starlette.responses import FileResponse
        from starlette.routing import Route
        
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
                        "framework": "aws_strands",
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
