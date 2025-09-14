"""Shared chat endpoints generator for web UI integration."""

import logging

logger = logging.getLogger(__name__)


class ChatEndpointsGenerator:
    """Generate chat endpoints for both localhost and docker pipelines."""

    def generate_chat_endpoints(
        self,
        framework_type: str,
        request_style: str = "starlette",
        deployment_type: str = "docker",
    ) -> str:
        """Generate chat endpoints for web UI integration.

        Args:
            framework_type: "adk", "strands", or "generic"
            request_style: "starlette" or "fastapi"
            deployment_type: "localhost" or "docker" - affects agent URL generation

        Returns:
            Generated chat endpoint code as string
        """
        if request_style == "fastapi":
            return self._generate_fastapi_chat_endpoints(deployment_type)
        else:
            return self._generate_starlette_chat_endpoints(deployment_type)

    def _generate_fastapi_chat_endpoints(self, deployment_type: str) -> str:
        """Generate FastAPI style chat endpoints with direct body parsing."""
        template = """
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
"""

        # Replace the agent URL based on deployment type
        if deployment_type == "localhost":
            return template.replace(
                "f'http://localhost:{os.getenv(\"AGENT_PORT\")}'",
                "f'http://localhost:{os.getenv(\"AGENT_PORT\")}'",
            )
        else:
            # Docker: Use 127.0.0.1 for internal container communication
            return template.replace(
                "f'http://localhost:{os.getenv(\"AGENT_PORT\")}'",
                "f'http://127.0.0.1:{os.getenv(\"AGENT_PORT\")}'",
            )

    def _generate_starlette_chat_endpoints(self, deployment_type: str) -> str:
        """Generate Starlette style chat endpoints with manual request parsing."""
        template = """
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
"""

        # Replace the agent URL based on deployment type
        if deployment_type == "localhost":
            return template.replace(
                "f'http://localhost:{os.getenv(\"AGENT_PORT\")}'",
                "f'http://localhost:{os.getenv(\"AGENT_PORT\")}'",
            )
        else:
            # Docker: Use 127.0.0.1 for internal container communication
            return template.replace(
                "f'http://localhost:{os.getenv(\"AGENT_PORT\")}'",
                "f'http://127.0.0.1:{os.getenv(\"AGENT_PORT\")}'",
            )
