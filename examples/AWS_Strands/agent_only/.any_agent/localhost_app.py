#!/usr/bin/env python3
"""AWS Strands A2A entrypoint for Minimal Strands Agent (localhost mode)."""

import logging
import os
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_agent():
    """Load the agent dynamically."""
    try:
        # We are in .any_agent/localhost_app.py
        # Go up to agent directory, then up to parent directory to import agent as module
        agent_parent_dir = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(agent_parent_dir))
        
        # Import the agent package from parent directory
        import agent_only
        
        if not hasattr(agent_only, 'root_agent'):
            raise ValueError("Agent package must have 'root_agent' variable exposed in __init__.py")
            
        return agent_only.root_agent
    except Exception as e:
        logger.error(f"Failed to load agent: {e}")
        raise

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
        logger.warning(f"Failed to upgrade agent for context isolation: {upgrade_error}")
    
    # Import Strands A2A server components
    from AWS_Strands.multiagent.a2a import A2AServer
    from any_agent.shared.strands_context_executor import ContextAwareStrandsA2AExecutor
    from a2a.server.request_handlers import DefaultRequestHandler
    from a2a.server.tasks import InMemoryTaskStore
    from a2a.server.apps import A2AStarletteApplication
    from a2a.types import AgentCapabilities, AgentCard, AgentSkill
    
    # Create Strands A2A server with custom executor
    logger.info(f"Creating Strands A2A server with context isolation for port 8045...")
    
    # Create custom executor
    custom_executor = ContextAwareStrandsA2AExecutor(root_agent)
    
    # Create agent card with capabilities and skills
    def generate_agent_card():
        capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
        skill = AgentSkill(
            id=f"minimal_strands_agent_skill",
            name=f"Minimal Strands Agent Agent", 
            description=f"AI agent built with AWS Strands framework",
            tags=["aws_strands", "ai-agent", "any-agent"],
            examples=[
                "Help me with my task",
                "What can you do?",
                "Process this request"
            ],
        )
        return AgentCard(
            name=f"Minimal Strands Agent Agent",
            description=f"Containerized AWS Strands agent",
            url=f"http://localhost:8045/",
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
    
    logger.info(f"✅ A2A server created for Minimal Strands Agent")
    
    # Build the ASGI app
    app = a2a_server.build()
    
    # Add health endpoint using Starlette routing
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    
    async def health_check(request):
        return JSONResponse({"status": "healthy", "service": "AWS_Strands-a2a-agent", "framework": "aws_strands"})
    
    # Add health route to the app routes
    health_route = Route("/health", health_check, methods=["GET"])
    app.routes.append(health_route)
    
    
    # Add chat endpoints for web UI integration
    try:
        import sys
        import os
        sys.path.insert(0, '/app')
        
        # Import the framework-specific chat handler
        from any_agent.api.chat_handler import A2AChatHandler
        
        # Create chat handler instance
        chat_handler = A2AChatHandler(timeout=300)
        
        # Add chat routes (Starlette style with manual request parsing)
        async def create_chat_session_endpoint(request):
            try:
                request_body = await request.json()
                session_id = request_body.get('session_id')
                agent_url = request_body.get('agent_url', f'http://localhost:{os.getenv("AGENT_PORT")}')
                
                if not session_id:
                    return JSONResponse({"success": False, "error": "session_id required"}, status_code=400)
                
                try:
                    result = await chat_handler.create_session(session_id, agent_url)
                    return JSONResponse(result)
                except Exception as e:
                    logger.error(f"Failed to create chat session: {e}")
                    return JSONResponse({"success": False, "error": str(e)}, status_code=500)
            except Exception as e:
                logger.error(f"Failed to parse request: {e}")
                return JSONResponse({"success": False, "error": "Invalid JSON"}, status_code=400)
        
        async def send_chat_message_endpoint(request):
            try:
                request_body = await request.json()
                session_id = request_body.get('session_id')
                message = request_body.get('message')
                
                if not session_id:
                    return JSONResponse({"success": False, "error": "session_id required"}, status_code=400)
                
                if not message:
                    return JSONResponse({"success": False, "error": "message required"}, status_code=400)
                
                try:
                    result = await chat_handler.send_message(session_id, message)
                    return JSONResponse(result)
                except Exception as e:
                    logger.error(f"Failed to send message: {e}")
                    return JSONResponse({"success": False, "error": str(e)}, status_code=500)
            except Exception as e:
                logger.error(f"Failed to parse request: {e}")
                return JSONResponse({"success": False, "error": "Invalid JSON"}, status_code=400)
        
        async def cleanup_chat_session_endpoint(request):
            try:
                request_body = await request.json()
                session_id = request_body.get('session_id')
                
                if not session_id:
                    return JSONResponse({"success": False, "error": "session_id required"}, status_code=400)
                
                try:
                    result = chat_handler.cleanup_session(session_id)
                    return JSONResponse(result)
                except Exception as e:
                    logger.error(f"Failed to cleanup session: {e}")
                    return JSONResponse({"success": False, "error": str(e)}, status_code=500)
            except Exception as e:
                logger.error(f"Failed to parse request: {e}")
                return JSONResponse({"success": False, "error": "Invalid JSON"}, status_code=400)
        
        async def cancel_chat_task_endpoint(request):
            try:
                request_body = await request.json()
                session_id = request_body.get('session_id')
                
                if not session_id:
                    return JSONResponse({"success": False, "error": "session_id required"}, status_code=400)
                
                try:
                    result = await chat_handler.cancel_task(session_id)
                    return JSONResponse(result)
                except Exception as e:
                    logger.error(f"Failed to cancel task: {e}")
                    return JSONResponse({"success": False, "error": str(e)}, status_code=500)
            except Exception as e:
                logger.error(f"Failed to parse request: {e}")
                return JSONResponse({"success": False, "error": "Invalid JSON"}, status_code=400)
        
        # Register routes (Starlette style)
        from starlette.routing import Route
        chat_create_route = Route("/chat/create-session", create_chat_session_endpoint, methods=["POST"])
        chat_send_route = Route("/chat/send-message", send_chat_message_endpoint, methods=["POST"])
        chat_cleanup_route = Route("/chat/cleanup-session", cleanup_chat_session_endpoint, methods=["POST"])
        chat_cancel_route = Route("/chat/cancel-task", cancel_chat_task_endpoint, methods=["POST"])
        app.routes.extend([chat_create_route, chat_send_route, chat_cleanup_route, chat_cancel_route])
        
        logger.info("Chat endpoints added successfully")
        
    except ImportError as import_error:
        logger.warning(f"Failed to import chat handler: {import_error}. Chat functionality will not be available.")
    except Exception as chat_setup_error:
        logger.warning(f"Failed to setup chat endpoints: {chat_setup_error}. Chat will not be available.")

    
    
    # Add static file serving if UI enabled
    from starlette.staticfiles import StaticFiles
    from starlette.responses import FileResponse, HTMLResponse, JSONResponse
    from starlette.routing import Route

    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")
        logger.info(f"📁 Mounted static files from {static_dir}")

        # Add route to serve index.html at root
        async def serve_ui(request):
            index_file = static_dir / "index.html"
            if index_file.exists():
                return FileResponse(index_file)
            else:
                return JSONResponse({
                    "agent": "Minimal Strands Agent",
                    "framework": "starlette",
                    "localhost_mode": True,
                    "status": "ui_enabled",
                    "error": "UI files not found"
                })

        # Add UI route at root
        ui_route = Route("/", serve_ui, methods=["GET"])
        app.routes.append(ui_route)
    else:
        logger.warning("📁 Static directory not found - UI files not served")

    
    logger.info(f"🌐 A2A server ready on port 8045")
    logger.info(f"📋 Agent card: http://localhost:8045/.well-known/agent-card.json")
    logger.info(f"🏥 Health check: http://localhost:8045/health")

except Exception as e:
    logger.error(f"❌ Failed to create A2A server: {e}")
    
    # Fallback minimal server
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    
    async def health_error(request):
        return JSONResponse({
            "status": "error",
            "agent_loaded": False,
            "framework": "aws_strands",
            "error": str(e),
            "localhost_mode": True
        })
    
    async def root_error(request):
        return JSONResponse({"error": "Agent failed to load", "details": str(e)})
    
    routes = [
        Route("/health", health_error, methods=["GET"]),
        Route("/", root_error, methods=["GET"]),
    ]
    
    app = Starlette(routes=routes)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8045)
