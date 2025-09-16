#!/usr/bin/env python3
"""Google ADK A2A entrypoint for Testing_Tessie (localhost mode)."""

import logging
import os
import sys
from pathlib import Path
from starlette.responses import JSONResponse
from starlette.routing import Route

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

# Load the ADK agent and create A2A app at module level
try:
    from google.adk.a2a.utils.agent_to_a2a import to_a2a
    
    # Load agent
    root_agent = load_agent()
    logger.info(f"✅ Loaded ADK agent: {root_agent}")
    
    # Upgrade agent for A2A context isolation
    try:
        from any_agent.core.context_aware_wrapper import upgrade_agent_for_context_isolation
        root_agent = upgrade_agent_for_context_isolation(root_agent)
        logger.info("✅ Agent upgraded for A2A context isolation")
    except Exception as upgrade_error:
        logger.warning(f"Failed to upgrade agent for context isolation: {upgrade_error}")
    
    # Create A2A app using Google's official utilities
    a2a_app = to_a2a(root_agent, port=8101)
    logger.info("✅ Created A2A app using Google ADK utilities")
    
    # Add health endpoint
    async def health_check(request):
        return JSONResponse({
            "status": "healthy",
            "agent_loaded": True,
            "framework": "google_adk",
            "a2a_enabled": True,
            "localhost_mode": True
        })
    
    health_route = Route("/health", health_check, methods=["GET"])
    a2a_app.routes.append(health_route)
    
    # Export the app for uvicorn
    app = a2a_app
    
    
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
    if True:
        from starlette.staticfiles import StaticFiles
        from starlette.responses import FileResponse
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
                    from starlette.responses import JSONResponse
                    return JSONResponse({
                        "agent": "Testing_Tessie",
                        "framework": "aws_strands",
                        "localhost_mode": True,
                        "status": "ui_enabled",
                        "error": "UI files not found"
                    })
            
            # Add UI route at root
            ui_route = Route("/", serve_ui, methods=["GET"])
            app.routes.append(ui_route)
        else:
            logger.warning("📁 Static directory not found - UI files not served")

    
except Exception as e:
    logger.error(f"❌ Failed to create A2A app: {e}")
    
    # Fallback minimal app
    from fastapi import FastAPI
    app = FastAPI(title="ADK Agent (Error State)")
    
    @app.get("/health")
    async def health_error():
        return {
            "status": "error",
            "agent_loaded": False,
            "framework": "google_adk",
            "error": str(e),
            "localhost_mode": True
        }
    
    @app.get("/")
    async def root_error():
        return {"error": "Agent failed to load", "details": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8101)
