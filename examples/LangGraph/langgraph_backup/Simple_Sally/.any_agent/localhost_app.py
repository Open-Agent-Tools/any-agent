#!/usr/bin/env python3
"""LangGraph native A2A server entrypoint for Simple Sally (localhost mode)."""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from fastapi import FastAPI
from fastapi.responses import JSONResponse

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
        import Simple_Sally
        
        if not hasattr(Simple_Sally, 'root_agent'):
            raise ValueError("Agent package must have 'root_agent' variable exposed in __init__.py")
            
        return Simple_Sally.root_agent
    except Exception as e:
        logger.error(f"Failed to load agent: {e}")
        raise

try:
    logger.info("Loading LangGraph agent...")
    root_agent = load_agent()
    logger.info("✅ LangGraph agent loaded successfully")

    # Import LangGraph Server components for native A2A support
    from langgraph.pregel import Pregel
    from langgraph.checkpoint.memory import MemorySaver

    # Validate that we have a proper LangGraph agent
    if not isinstance(root_agent, Pregel):
        logger.warning(f"Agent is not a LangGraph Pregel instance: {type(root_agent)}")
        logger.info("Attempting to use agent as-is for compatibility")

    # Create FastAPI app with LangGraph's native A2A capabilities
    app = FastAPI(
        title=f"Simple Sally LangGraph Agent",
        description="LangGraph agent with native A2A protocol support",
        version="1.0.0"
    )

    # Add health endpoint
    @app.get("/health")
    async def health_check():
        return JSONResponse({
            "status": "healthy",
            "agent_loaded": True,
            "framework": "langgraph",
            "a2a_enabled": True,
            "localhost_mode": True,
            "agent_type": str(type(root_agent).__name__)
        })

    # Native A2A endpoint implementation using LangGraph patterns
    @app.post("/a2a/{assistant_id}")
    async def a2a_endpoint(assistant_id: str, request: Dict[str, Any]):
        """Native A2A endpoint for LangGraph agent."""
        try:
            logger.info(f"A2A request for assistant {assistant_id}: {request}")

            # Extract message from A2A request
            message_content = request.get("params", {}).get("message", {}).get("content", "")
            if not message_content:
                return JSONResponse(
                    status_code=400,
                    content={"error": "No message content found in A2A request"}
                )

            # Create thread configuration for LangGraph
            thread_id = request.get("params", {}).get("thread_id", "default")
            config = {"configurable": {"thread_id": thread_id}}

            # Prepare messages in LangGraph format
            messages = [{"role": "user", "content": message_content}]

            # Execute LangGraph agent
            if hasattr(root_agent, 'invoke'):
                response = root_agent.invoke({"messages": messages}, config)
            elif hasattr(root_agent, 'stream'):
                # For streaming agents, get the final result
                result = None
                for chunk in root_agent.stream({"messages": messages}, config):
                    result = chunk
                response = result
            else:
                logger.error(f"Agent does not have invoke or stream method: {type(root_agent)}")
                return JSONResponse(
                    status_code=500,
                    content={"error": "Agent does not support expected execution methods"}
                )

            # Extract response content
            if isinstance(response, dict):
                if "messages" in response and response["messages"]:
                    last_message = response["messages"][-1]
                    if hasattr(last_message, 'content'):
                        response_content = last_message.content
                    elif isinstance(last_message, dict) and 'content' in last_message:
                        response_content = last_message['content']
                    else:
                        response_content = str(last_message)
                else:
                    response_content = str(response)
            else:
                response_content = str(response)

            # Return A2A compliant response
            return JSONResponse({
                "jsonrpc": "2.0",
                "result": {
                    "message": {
                        "content": response_content,
                        "role": "assistant"
                    }
                },
                "id": request.get("id", 1)
            })

        except Exception as e:
            logger.error(f"A2A endpoint error: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": "Internal error",
                        "data": str(e)
                    },
                    "id": request.get("id", 1)
                }
            )

    # Automatic Agent Card discovery endpoint (LangGraph native feature)
    @app.get("/.well-known/agent-card.json")
    async def agent_card():
        """LangGraph native Agent Card endpoint."""
        return JSONResponse({
            "name": f"Simple Sally",
            "description": f"LangGraph agent with native A2A protocol support",
            "version": "1.0.0",
            "framework": "langgraph",
            "url": f"http://localhost:8065/",
            "a2a_endpoint": f"/a2a/simple_sally",
            "capabilities": {
                "streaming": True,
                "stateful": True,
                "multi_turn": True
            },
            "defaultInputModes": ["text"],
            "defaultOutputModes": ["text"],
            "skills": [{
                "id": f"simple_sally_skill",
                "name": f"Simple Sally Skill",
                "description": f"LangGraph agent with stateful conversation and tool usage capabilities",
                "tags": ["langgraph", "ai-agent", "conversational", "stateful"],
                "examples": [
                    "What's the weather in San Francisco?",
                    "Calculate 25 * 17 + 143",
                    "What time is it now?",
                    "Remember that I prefer morning meetings"
                ]
            }],
            "localhost_mode": True
        })

    
    # Add chat endpoints for web UI integration
    try:
        import sys
        import os
        sys.path.insert(0, '/app')
        
        # Import the framework-specific chat handler
        from any_agent.api.chat_handler import A2AChatHandler
        
        # Create chat handler instance
        chat_handler = A2AChatHandler(timeout=300)
        
        # Add chat routes (FastAPI style with Pydantic body parsing)
        async def create_chat_session_endpoint(request_body: dict):
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
        
        async def send_chat_message_endpoint(request_body: dict):
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
        
        async def cleanup_chat_session_endpoint(request_body: dict):
            session_id = request_body.get('session_id')
            
            if not session_id:
                return JSONResponse({"success": False, "error": "session_id required"}, status_code=400)
            
            try:
                result = chat_handler.cleanup_session(session_id)
                return JSONResponse(result)
            except Exception as e:
                logger.error(f"Failed to cleanup session: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)
        
        async def cancel_chat_task_endpoint(request_body: dict):
            session_id = request_body.get('session_id')
            
            if not session_id:
                return JSONResponse({"success": False, "error": "session_id required"}, status_code=400)
            
            try:
                result = await chat_handler.cancel_task(session_id)
                return JSONResponse(result)
            except Exception as e:
                logger.error(f"Failed to cancel task: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)
        
        # Register routes (FastAPI style)
        app.post("/chat/create-session")(create_chat_session_endpoint)
        app.post("/chat/send-message")(send_chat_message_endpoint)
        app.post("/chat/cleanup-session")(cleanup_chat_session_endpoint)
        app.post("/chat/cancel-task")(cancel_chat_task_endpoint)
        
        logger.info("Chat endpoints added successfully")
        
    except ImportError as import_error:
        logger.warning(f"Failed to import chat handler: {import_error}. Chat functionality will not be available.")
    except Exception as chat_setup_error:
        logger.warning(f"Failed to setup chat endpoints: {chat_setup_error}. Chat will not be available.")


    
    # Add static file serving if UI enabled
    from fastapi.responses import HTMLResponse, FileResponse
    from fastapi.staticfiles import StaticFiles

    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")
        logger.info(f"📁 Mounted static files from {static_dir}")

        @app.get("/")
        @app.get("/describe")
        async def serve_ui():
            """Serve UI at root endpoint."""
            index_file = static_dir / "index.html"
            if index_file.exists():
                return FileResponse(index_file)
            else:
                return HTMLResponse(
                    "<h1>UI Not Available</h1><p>React SPA could not be loaded.</p>",
                    status_code=503
                )
    else:
        logger.warning("📁 Static directory not found - UI files not served")


    logger.info(f"🌐 LangGraph A2A server ready on port 8065")
    logger.info(f"📋 Agent card: http://localhost:8065/.well-known/agent-card.json")
    logger.info(f"🤖 A2A endpoint: http://localhost:8065/a2a/simple_sally")
    logger.info(f"🏥 Health check: http://localhost:8065/health")

except Exception as e:
    logger.error(f"❌ Failed to create LangGraph A2A server: {e}")

    # Fallback minimal server
    from fastapi import FastAPI
    app = FastAPI(title="LangGraph Agent (Error State)")

    @app.get("/health")
    async def health_error():
        return JSONResponse({
            "status": "error",
            "agent_loaded": False,
            "framework": "langgraph",
            "error": str(e),
            "localhost_mode": True
        })



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8065)
