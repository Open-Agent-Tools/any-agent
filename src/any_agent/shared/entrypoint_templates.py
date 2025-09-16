"""Shared entrypoint templates for both localhost and Docker pipelines."""

import logging
from pathlib import Path
from dataclasses import dataclass

from .chat_endpoints_generator import ChatEndpointsGenerator
from .ui_routes_generator import UIRoutesGenerator

logger = logging.getLogger(__name__)


@dataclass
class EntrypointContext:
    """Context for generating entrypoint templates."""

    agent_name: str
    agent_path: Path
    framework: str
    port: int
    add_ui: bool = False
    deployment_type: str = "docker"  # "docker" or "localhost"


class UnifiedEntrypointGenerator:
    """Generate entrypoints for all frameworks and deployment types."""

    def __init__(self):
        self.chat_generator = ChatEndpointsGenerator()
        self.ui_generator = UIRoutesGenerator()

    def generate_entrypoint(self, context: EntrypointContext) -> str:
        """Generate framework-specific entrypoint based on context."""
        if context.framework.lower() == "google_adk":
            return self._generate_adk_entrypoint(context)
        elif context.framework.lower() == "aws_strands":
            return self._generate_strands_entrypoint(context)
        else:
            return self._generate_generic_entrypoint(context)

    def _generate_agent_loader(self, context: EntrypointContext) -> str:
        """Generate agent loading code based on deployment type."""
        if context.deployment_type == "docker":
            return f"""def load_agent():
    \"\"\"Load the agent dynamically.\"\"\"
    try:
        sys.path.insert(0, '/app')
        import {context.agent_path.name}
        
        if not hasattr({context.agent_path.name}, 'root_agent'):
            raise ValueError("Agent package must have 'root_agent' variable exposed in __init__.py")
            
        return {context.agent_path.name}.root_agent
    except Exception as e:
        logger.error(f"Failed to load agent: {{e}}")
        raise"""
        else:
            # Use absolute path from context since __file__ isn't reliable in uvicorn
            agent_parent_dir = str(context.agent_path.parent.resolve())
            return f"""def load_agent():
    \"\"\"Load the agent dynamically.\"\"\"
    try:
        # Use absolute path to agent parent directory
        agent_parent_dir = "{agent_parent_dir}"
        sys.path.insert(0, agent_parent_dir)

        # Import the agent package
        import {context.agent_path.name}

        if not hasattr({context.agent_path.name}, 'root_agent'):
            raise ValueError("Agent package must have 'root_agent' variable exposed in __init__.py")

        return {context.agent_path.name}.root_agent
    except Exception as e:
        logger.error(f"Failed to load agent: {{e}}")
        raise"""

    def _generate_adk_entrypoint(self, context: EntrypointContext) -> str:
        """Generate Google ADK specific entrypoint."""
        agent_loader = self._generate_agent_loader(context)
        request_style = "fastapi" if context.framework == "generic" else "starlette"
        chat_endpoints = self.chat_generator.generate_chat_endpoints(
            "adk", request_style, context.deployment_type
        )

        if context.deployment_type == "localhost":
            ui_routes = self.ui_generator.generate_localhost_ui_routes(
                context.add_ui, context.port, context.agent_name
            )
        else:
            ui_routes = self.ui_generator.generate_ui_routes(
                context.add_ui, "adk", request_style
            )

        mode_suffix = (
            " (localhost mode)" if context.deployment_type == "localhost" else ""
        )

        entrypoint_content = f'''#!/usr/bin/env python3
"""Google ADK A2A entrypoint for {context.agent_name}{mode_suffix}."""

import logging
import os
import sys
from pathlib import Path
from starlette.responses import JSONResponse
from starlette.routing import Route

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

{agent_loader}

# Load the ADK agent and create A2A app at module level
try:
    from google.adk.a2a.utils.agent_to_a2a import to_a2a
    
    # Load agent
    root_agent = load_agent()
    logger.info(f"✅ Loaded ADK agent: {{root_agent}}")
    
    # Upgrade agent for A2A context isolation
    try:
        from any_agent.core.context_aware_wrapper import upgrade_agent_for_context_isolation
        root_agent = upgrade_agent_for_context_isolation(root_agent)
        logger.info("✅ Agent upgraded for A2A context isolation")
    except Exception as upgrade_error:
        logger.warning(f"Failed to upgrade agent for context isolation: {{upgrade_error}}")
    
    # Create A2A app using Google's official utilities
    a2a_app = to_a2a(root_agent, port={context.port})
    logger.info("✅ Created A2A app using Google ADK utilities")
    
    # Add health endpoint
    async def health_check(request):
        return JSONResponse({{
            "status": "healthy",
            "agent_loaded": True,
            "framework": "google_adk",
            "a2a_enabled": True,
            "localhost_mode": {str(context.deployment_type == "localhost").title()}
        }})
    
    health_route = Route("/health", health_check, methods=["GET"])
    a2a_app.routes.append(health_route)
    
    # Export the app for uvicorn
    app = a2a_app
    
    {chat_endpoints}
    
    {ui_routes}
    
except Exception as e:
    logger.error(f"❌ Failed to create A2A app: {{e}}")
    
    # Fallback minimal app
    from fastapi import FastAPI
    app = FastAPI(title="ADK Agent (Error State)")
    
    @app.get("/health")
    async def health_error():
        return {{
            "status": "error",
            "agent_loaded": False,
            "framework": "google_adk",
            "error": "Agent loading failed",
            "localhost_mode": {str(context.deployment_type == "localhost").title()}
        }}
    
    @app.get("/")
    async def root_error():
        return {{"error": "Agent failed to load", "details": "Agent loading failed"}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port={context.port})
'''
        return entrypoint_content

    def _generate_strands_entrypoint(self, context: EntrypointContext) -> str:
        """Generate AWS Strands specific entrypoint."""
        agent_loader = self._generate_agent_loader(context)
        request_style = "starlette"  # Strands uses Starlette
        chat_endpoints = self.chat_generator.generate_chat_endpoints(
            "strands", request_style, context.deployment_type
        )

        if context.deployment_type == "localhost":
            ui_routes = self.ui_generator.generate_localhost_ui_routes(
                context.add_ui, context.port, context.agent_name
            )
        else:
            ui_routes = self.ui_generator.generate_ui_routes(
                context.add_ui, "strands", request_style
            )

        mode_suffix = (
            " (localhost mode)" if context.deployment_type == "localhost" else ""
        )

        entrypoint_content = f'''#!/usr/bin/env python3
"""AWS Strands A2A entrypoint for {context.agent_name}{mode_suffix}."""

import logging
import os
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

{agent_loader}

try:
    logger.info("Loading Strands agent...")
    root_agent = load_agent()
    logger.info("Strands agent loaded successfully")
    
    # Upgrade agent for A2A context isolation
    try:
        from any_agent.core.context_aware_wrapper import upgrade_agent_for_context_isolation
        root_agent = upgrade_agent_for_context_isolation(root_agent)
        logger.info("✅ Agent upgraded for A2A context isolation")
    except Exception as upgrade_error:
        logger.warning(f"Failed to upgrade agent for context isolation: {{upgrade_error}}")
    
    # Import Strands A2A server components
    from strands.multiagent.a2a import A2AServer
    from any_agent.shared.strands_context_executor import ContextAwareStrandsA2AExecutor
    from a2a.server.request_handlers import DefaultRequestHandler
    from a2a.server.tasks import InMemoryTaskStore
    from a2a.server.apps import A2AStarletteApplication
    from a2a.types import AgentCapabilities, AgentCard, AgentSkill
    
    # Create Strands A2A server with custom executor
    logger.info(f"Creating Strands A2A server with context isolation for port {context.port}...")
    
    # Create custom executor
    custom_executor = ContextAwareStrandsA2AExecutor(root_agent)
    
    # Create agent card with capabilities and skills
    def generate_agent_card():
        capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
        skill = AgentSkill(
            id=f"{context.agent_name.lower().replace(" ", "_")}_skill",
            name=f"{context.agent_name} Agent", 
            description=f"AI agent built with AWS Strands framework",
            tags=["aws_strands", "ai-agent", "any-agent"],
            examples=[
                "Help me with my task",
                "What can you do?",
                "Process this request"
            ],
        )
        return AgentCard(
            name=f"{context.agent_name} Agent",
            description=f"Containerized AWS Strands agent",
            url=f"http://localhost:{context.port}/",
            version="1.0.0",
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            capabilities=capabilities,
            skills=[skill],
        )
    
    # Create request handler with custom executor
    request_handler = DefaultRequestHandler(
        agent_executor=custom_executor,
        task_store=InMemoryTaskStore(),
    )
    
    # Create A2A Starlette server with agent card and request handler
    logger.info(f"Creating A2AStarletteApplication with agent card...")
    a2a_server = A2AStarletteApplication(
        agent_card=generate_agent_card(),
        http_handler=request_handler
    )
    
    logger.info(f"✅ A2A server created for {context.agent_name}")
    
    # Build the ASGI app
    app = a2a_server.build()
    
    # Add health endpoint using Starlette routing
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    
    async def health_check(request):
        return JSONResponse({{"status": "healthy", "service": "strands-a2a-agent", "framework": "aws_strands"}})
    
    # Add health route to the app routes
    health_route = Route("/health", health_check, methods=["GET"])
    app.routes.append(health_route)
    
    {chat_endpoints}
    
    {ui_routes}
    
    logger.info(f"🌐 A2A server ready on port {context.port}")
    logger.info(f"📋 Agent card: http://localhost:{context.port}/.well-known/agent-card.json")
    logger.info(f"🏥 Health check: http://localhost:{context.port}/health")

except Exception as e:
    logger.error(f"❌ Failed to create A2A server: {{e}}")
    
    # Fallback minimal server
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    
    async def health_error(request):
        return JSONResponse({{
            "status": "error",
            "agent_loaded": False,
            "framework": "aws_strands",
            "error": "Agent loading failed",
            "localhost_mode": {str(context.deployment_type == "localhost").title()}
        }})
    
    async def root_error(request):
        return JSONResponse({{"error": "Agent failed to load", "details": str(e)}})
    
    routes = [
        Route("/health", health_error, methods=["GET"]),
        Route("/", root_error, methods=["GET"]),
    ]
    
    app = Starlette(routes=routes)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port={context.port})
'''
        return entrypoint_content

    def _generate_generic_entrypoint(self, context: EntrypointContext) -> str:
        """Generate generic FastAPI entrypoint for other frameworks."""
        agent_loader = self._generate_agent_loader(context)
        request_style = "fastapi"
        chat_endpoints = self.chat_generator.generate_chat_endpoints(
            "generic", request_style, context.deployment_type
        )
        ui_routes = self.ui_generator.generate_ui_routes(
            context.add_ui, "generic", request_style
        )

        mode_suffix = (
            " (localhost mode)" if context.deployment_type == "localhost" else ""
        )

        entrypoint_content = f'''#!/usr/bin/env python3
"""Generic A2A entrypoint for {context.agent_name}{mode_suffix}."""

import logging
import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

{agent_loader}

try:
    logger.info("Loading agent...")
    root_agent = load_agent()
    logger.info("Agent loaded successfully")
    
    # Upgrade agent for A2A context isolation
    try:
        from any_agent.core.context_aware_wrapper import upgrade_agent_for_context_isolation
        root_agent = upgrade_agent_for_context_isolation(root_agent)
        logger.info("✅ Agent upgraded for A2A context isolation")
    except Exception as upgrade_error:
        logger.warning(f"Failed to upgrade agent for context isolation: {{upgrade_error}}")
    
    # Create FastAPI app
    app = FastAPI(title="{context.agent_name}", description="Generic A2A Agent")
    
    # Add health endpoint
    @app.get("/health")
    async def health_check():
        return JSONResponse({{"status": "healthy", "service": "generic-a2a-agent", "framework": "{context.framework}"}})
    
    # Basic A2A endpoints
    @app.post("/message:send")
    async def send_message(request: dict):
        # Basic implementation - would need framework-specific logic
        return JSONResponse({{"message": "Generic response from {context.agent_name}"}})
    
    @app.get("/.well-known/agent-card.json")
    async def agent_card():
        return JSONResponse({{
            "name": "{context.agent_name}",
            "framework": "{context.framework}",
            "version": "1.0.0",
            "localhost_mode": {str(context.deployment_type == "localhost").title()},
            "endpoints": {{
                "message:send": "/message:send"
            }}
        }})
    
    {chat_endpoints}
    
    {ui_routes}
    
except Exception as e:
    logger.error(f"Failed to create generic A2A app: {{e}}")
    raise


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port={context.port})
'''
        return entrypoint_content
