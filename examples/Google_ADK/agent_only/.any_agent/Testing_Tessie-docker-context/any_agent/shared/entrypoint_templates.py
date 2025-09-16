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
        elif context.framework.lower() == "langchain":
            return self._generate_langchain_entrypoint(context)
        elif context.framework.lower() == "langgraph":
            return self._generate_langgraph_entrypoint(context)
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
            return f"""def load_agent():
    \"\"\"Load the agent dynamically.\"\"\"
    try:
        # We are in .any_agent/localhost_app.py
        # Go up to agent directory, then up to parent directory to import agent as module
        agent_parent_dir = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(agent_parent_dir))
        
        # Import the agent package from parent directory
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
            "Google_ADK", request_style, context.deployment_type
        )

        if context.deployment_type == "localhost":
            ui_routes = self.ui_generator.generate_localhost_ui_routes(
                context.add_ui, context.port, context.agent_name
            )
        else:
            ui_routes = self.ui_generator.generate_ui_routes(
                context.add_ui, "Google_ADK", request_style
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
    from google.Google_ADK.a2a.utils.agent_to_a2a import to_a2a
    
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
            "error": str(e),
            "localhost_mode": {str(context.deployment_type == "localhost").title()}
        }}
    
    @app.get("/")
    async def root_error():
        return {{"error": "Agent failed to load", "details": str(e)}}


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
            "AWS_Strands", request_style, context.deployment_type
        )

        if context.deployment_type == "localhost":
            ui_routes = self.ui_generator.generate_localhost_ui_routes(
                context.add_ui, context.port, context.agent_name
            )
        else:
            ui_routes = self.ui_generator.generate_ui_routes(
                context.add_ui, "AWS_Strands", request_style
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
    from AWS_Strands.multiagent.a2a import A2AServer
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
        return JSONResponse({{"status": "healthy", "service": "AWS_Strands-a2a-agent", "framework": "aws_strands"}})
    
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
            "error": str(e),
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

    def _generate_langchain_entrypoint(self, context: EntrypointContext) -> str:
        """Generate LangChain-specific A2A entrypoint with proper agent card."""
        agent_loader = self._generate_agent_loader(context)
        request_style = "fastapi"
        chat_endpoints = self.chat_generator.generate_chat_endpoints(
            "langchain", request_style, context.deployment_type
        )
        ui_routes = self.ui_generator.generate_ui_routes(
            context.add_ui, "langchain", request_style
        )

        mode_suffix = (
            " (localhost mode)" if context.deployment_type == "localhost" else ""
        )

        entrypoint_content = f'''#!/usr/bin/env python3
"""LangChain A2A entrypoint for {context.agent_name}{mode_suffix}."""

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
    logger.info("Loading LangChain agent...")
    root_agent = load_agent()
    logger.info("✅ LangChain agent loaded successfully")

    # Create FastAPI app
    app = FastAPI(title="{context.agent_name}", description="LangChain A2A Agent")

    # Add health endpoint
    @app.get("/health")
    async def health_check():
        return JSONResponse({{"status": "healthy", "service": "langchain-a2a-agent", "framework": "langchain"}})

    # A2A endpoints
    @app.post("/message:send")
    async def send_message(request: dict):
        try:
            # LangChain agent invocation
            message = request.get("message", {{}}).get("content", "")
            if not message:
                return JSONResponse({{"error": "No message content provided"}})

            # Invoke LangChain agent with proper message format
            response = root_agent.invoke({{
                "messages": [{{"role": "user", "content": message}}]
            }})

            # Extract response from LangChain format
            if "messages" in response and response["messages"]:
                last_message = response["messages"][-1]
                content = getattr(last_message, 'content', str(last_message))
            else:
                content = str(response)

            return JSONResponse({{
                "message": {{
                    "role": "assistant",
                    "content": content
                }}
            }})
        except Exception as e:
            logger.error(f"LangChain agent error: {{e}}")
            return JSONResponse({{"error": f"Agent processing failed: {{str(e)}}"}}, status_code=500)

    @app.get("/.well-known/agent-card.json")
    async def agent_card():
        actual_port = os.getenv('AGENT_PORT', {context.port})
        return JSONResponse({{
            "name": "{context.agent_name}",
            "description": "LangChain agent with tool capabilities",
            "url": f"http://localhost:{{actual_port}}/",
            "framework": "langchain",
            "version": "1.0.0",
            "localhost_mode": {str(context.deployment_type == "localhost").title()},
            "defaultInputModes": ["text"],
            "defaultOutputModes": ["text"],
            "capabilities": {{
                "streaming": False,
                "pushNotifications": False,
                "tools": True
            }},
            "skills": [{{
                "id": "langchain_agent_skill",
                "name": "LangChain Agent",
                "description": "AI agent built with LangChain framework supporting tools and reasoning",
                "tags": ["langchain", "tools", "reasoning", "any-agent"]
            }}],
            "endpoints": {{
                "message:send": "/message:send"
            }}
        }})

    {chat_endpoints}

    {ui_routes}

    logger.info(f"🌐 LangChain A2A server ready on port {context.port}")
    logger.info(f"📋 Agent card: http://localhost:{context.port}/.well-known/agent-card.json")
    logger.info(f"🏥 Health check: http://localhost:{context.port}/health")

except Exception as e:
    logger.error(f"❌ Failed to create LangChain A2A server: {{e}}")
    raise


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port={context.port})
'''
        return entrypoint_content

    def _generate_langgraph_entrypoint(self, context: EntrypointContext) -> str:
        """Generate LangGraph-specific A2A entrypoint with proper agent card."""
        agent_loader = self._generate_agent_loader(context)
        request_style = "fastapi"
        chat_endpoints = self.chat_generator.generate_chat_endpoints(
            "langgraph", request_style, context.deployment_type
        )
        ui_routes = self.ui_generator.generate_ui_routes(
            context.add_ui, "langgraph", request_style
        )

        mode_suffix = (
            " (localhost mode)" if context.deployment_type == "localhost" else ""
        )

        entrypoint_content = f'''#!/usr/bin/env python3
"""LangGraph A2A entrypoint for {context.agent_name}{mode_suffix}."""

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
    logger.info("Loading LangGraph agent...")
    root_agent = load_agent()
    logger.info("✅ LangGraph agent loaded successfully")

    # Create FastAPI app
    app = FastAPI(title="{context.agent_name}", description="LangGraph A2A Agent")

    # Add health endpoint
    @app.get("/health")
    async def health_check():
        return JSONResponse({{"status": "healthy", "service": "langgraph-a2a-agent", "framework": "langgraph"}})

    # A2A endpoints
    @app.post("/message:send")
    async def send_message(request: dict):
        try:
            # LangGraph agent invocation
            message = request.get("message", {{}}).get("content", "")
            if not message:
                return JSONResponse({{"error": "No message content provided"}})

            # Invoke LangGraph agent with proper message format
            response = root_agent.invoke({{
                "messages": [{{"role": "user", "content": message}}]
            }})

            # Extract response from LangGraph format
            if "messages" in response and response["messages"]:
                last_message = response["messages"][-1]
                content = getattr(last_message, 'content', str(last_message))
            else:
                content = str(response)

            return JSONResponse({{
                "message": {{
                    "role": "assistant",
                    "content": content
                }}
            }})
        except Exception as e:
            logger.error(f"LangGraph agent error: {{e}}")
            return JSONResponse({{"error": f"Agent processing failed: {{str(e)}}"}}, status_code=500)

    @app.get("/.well-known/agent-card.json")
    async def agent_card():
        actual_port = os.getenv('AGENT_PORT', {context.port})
        return JSONResponse({{
            "name": "{context.agent_name}",
            "description": "LangGraph agent with stateful workflow capabilities",
            "url": f"http://localhost:{{actual_port}}/",
            "framework": "langgraph",
            "version": "1.0.0",
            "localhost_mode": {str(context.deployment_type == "localhost").title()},
            "defaultInputModes": ["text"],
            "defaultOutputModes": ["text"],
            "capabilities": {{
                "streaming": True,
                "pushNotifications": False,
                "stateful": True,
                "workflows": True
            }},
            "skills": [{{
                "id": "langgraph_agent_skill",
                "name": "LangGraph Agent",
                "description": "AI agent built with LangGraph framework supporting stateful workflows and multi-step reasoning",
                "tags": ["langgraph", "workflows", "stateful", "multi-step", "any-agent"]
            }}],
            "endpoints": {{
                "message:send": f"http://localhost:{{actual_port}}/message:send"
            }}
        }})

    {chat_endpoints}

    {ui_routes}

    logger.info(f"🌐 LangGraph A2A server ready on port {context.port}")
    logger.info(f"📋 Agent card: http://localhost:{context.port}/.well-known/agent-card.json")
    logger.info(f"🏥 Health check: http://localhost:{context.port}/health")

except Exception as e:
    logger.error(f"❌ Failed to create LangGraph A2A server: {{e}}")
    raise


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port={context.port})
'''
        return entrypoint_content
