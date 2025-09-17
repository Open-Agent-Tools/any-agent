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

        # Import the framework-specific chat handler and URL builder
        from any_agent.api.chat_handler import A2AChatHandler
        from any_agent.shared.url_builder import get_url_builder

        # Create chat handler instance
        chat_handler = A2AChatHandler(timeout=300)
        url_builder = get_url_builder("{deployment_type}")

        # Add chat routes (FastAPI style with Pydantic body parsing)
        async def create_chat_session_endpoint(request_body: dict):
            session_id = request_body.get('session_id')
            agent_url = url_builder.agent_url_with_fallback(request_body.get('agent_url'))

            if not session_id:
                return JSONResponse({{"success": False, "error": "session_id required"}}, status_code=400)

            try:
                result = await chat_handler.create_session(session_id, agent_url)
                return JSONResponse(result)
            except Exception as error:
                logger.error(f"Failed to create chat session: {{error}}")
                return JSONResponse({{"success": False, "error": str(error)}}, status_code=500)

        async def send_chat_message_endpoint(request_body: dict):
            session_id = request_body.get('session_id')
            message = request_body.get('message')

            if not session_id:
                return JSONResponse({{"success": False, "error": "session_id required"}}, status_code=400)

            if not message:
                return JSONResponse({{"success": False, "error": "message required"}}, status_code=400)

            try:
                result = await chat_handler.send_message(session_id, message)
                return JSONResponse(result)
            except Exception as error:
                logger.error(f"Failed to send message: {{error}}")
                return JSONResponse({{"success": False, "error": str(error)}}, status_code=500)

        async def cleanup_chat_session_endpoint(request_body: dict):
            session_id = request_body.get('session_id')

            if not session_id:
                return JSONResponse({{"success": False, "error": "session_id required"}}, status_code=400)

            try:
                result = chat_handler.cleanup_session(session_id)
                return JSONResponse(result)
            except Exception as error:
                logger.error(f"Failed to cleanup session: {{error}}")
                return JSONResponse({{"success": False, "error": str(error)}}, status_code=500)

        async def cancel_chat_task_endpoint(request_body: dict):
            session_id = request_body.get('session_id')

            if not session_id:
                return JSONResponse({{"success": False, "error": "session_id required"}}, status_code=400)

            try:
                result = await chat_handler.cancel_task(session_id)
                return JSONResponse(result)
            except Exception as error:
                logger.error(f"Failed to cancel task: {{error}}")
                return JSONResponse({{"success": False, "error": str(error)}}, status_code=500)

        # Register chat endpoints
        app.post("/chat/create-session")(create_chat_session_endpoint)
        app.post("/chat/send-message")(send_chat_message_endpoint)
        app.post("/chat/cleanup-session")(cleanup_chat_session_endpoint)
        app.post("/chat/cancel-task")(cancel_chat_task_endpoint)

        logger.info("Chat endpoints added successfully")

    except ImportError as import_error:
        logger.warning(f"Failed to import chat handler: {{import_error}}. Chat functionality will not be available.")
    except Exception as chat_setup_error:
        logger.warning(f"Failed to setup chat endpoints: {{chat_setup_error}}. Chat will not be available.")
"""
        return template.format(deployment_type=deployment_type)

    def _generate_starlette_chat_endpoints(self, deployment_type: str) -> str:
        """Generate Starlette style chat endpoints with manual request parsing."""
        template = """
    # Add chat endpoints for web UI integration
    try:
        import sys
        import os
        import json
        sys.path.insert(0, '/app')

        # Import the framework-specific chat handler and URL builder
        from any_agent.api.chat_handler import A2AChatHandler
        from any_agent.shared.url_builder import get_url_builder
        from starlette.responses import JSONResponse

        # Create chat handler instance
        chat_handler = A2AChatHandler(timeout=300)
        url_builder = get_url_builder("{deployment_type}")

        # Add chat routes (Starlette style with manual request parsing)
        async def create_chat_session_endpoint(request):
            try:
                request_body = await request.json()
                session_id = request_body.get('session_id')
                agent_url = url_builder.agent_url_with_fallback(request_body.get('agent_url'))

                if not session_id:
                    return JSONResponse({{"success": False, "error": "session_id required"}}, status_code=400)

                try:
                    result = await chat_handler.create_session(session_id, agent_url)
                    return JSONResponse(result)
                except Exception as error:
                    logger.error(f"Failed to create chat session: {{error}}")
                    return JSONResponse({{"success": False, "error": str(error)}}, status_code=500)
            except Exception as error:
                logger.error(f"Failed to parse request: {{error}}")
                return JSONResponse({{"success": False, "error": "Invalid JSON"}}, status_code=400)

        async def send_chat_message_endpoint(request):
            try:
                request_body = await request.json()
                session_id = request_body.get('session_id')
                message = request_body.get('message')

                if not session_id:
                    return JSONResponse({{"success": False, "error": "session_id required"}}, status_code=400)

                if not message:
                    return JSONResponse({{"success": False, "error": "message required"}}, status_code=400)

                try:
                    result = await chat_handler.send_message(session_id, message)
                    return JSONResponse(result)
                except Exception as error:
                    logger.error(f"Failed to send message: {{error}}")
                    return JSONResponse({{"success": False, "error": str(error)}}, status_code=500)
            except Exception as error:
                logger.error(f"Failed to parse request: {{error}}")
                return JSONResponse({{"success": False, "error": "Invalid JSON"}}, status_code=400)

        async def cleanup_chat_session_endpoint(request):
            try:
                request_body = await request.json()
                session_id = request_body.get('session_id')

                if not session_id:
                    return JSONResponse({{"success": False, "error": "session_id required"}}, status_code=400)

                try:
                    result = chat_handler.cleanup_session(session_id)
                    return JSONResponse(result)
                except Exception as error:
                    logger.error(f"Failed to cleanup session: {{error}}")
                    return JSONResponse({{"success": False, "error": str(error)}}, status_code=500)
            except Exception as error:
                logger.error(f"Failed to parse request: {{error}}")
                return JSONResponse({{"success": False, "error": "Invalid JSON"}}, status_code=400)

        async def cancel_chat_task_endpoint(request):
            try:
                request_body = await request.json()
                session_id = request_body.get('session_id')

                if not session_id:
                    return JSONResponse({{"success": False, "error": "session_id required"}}, status_code=400)

                try:
                    result = await chat_handler.cancel_task(session_id)
                    return JSONResponse(result)
                except Exception as error:
                    logger.error(f"Failed to cancel task: {{error}}")
                    return JSONResponse({{"success": False, "error": str(error)}}, status_code=500)
            except Exception as error:
                logger.error(f"Failed to parse request: {{error}}")
                return JSONResponse({{"success": False, "error": "Invalid JSON"}}, status_code=400)

        # Register chat endpoints
        from starlette.routing import Route
        chat_create_route = Route("/chat/create-session", create_chat_session_endpoint, methods=["POST"])
        chat_send_route = Route("/chat/send-message", send_chat_message_endpoint, methods=["POST"])
        chat_cleanup_route = Route("/chat/cleanup-session", cleanup_chat_session_endpoint, methods=["POST"])
        chat_cancel_route = Route("/chat/cancel-task", cancel_chat_task_endpoint, methods=["POST"])
        app.routes.extend([chat_create_route, chat_send_route, chat_cleanup_route, chat_cancel_route])

        logger.info("Chat endpoints added successfully")

    except ImportError as import_error:
        logger.warning(f"Failed to import chat handler: {{import_error}}. Chat functionality will not be available.")
    except Exception as chat_setup_error:
        logger.warning(f"Failed to setup chat endpoints: {{chat_setup_error}}. Chat will not be available.")
"""
        return template.format(deployment_type=deployment_type)
