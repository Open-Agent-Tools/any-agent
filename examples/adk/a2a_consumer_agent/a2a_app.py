from google.adk.a2a.utils.agent_to_a2a import to_a2a
from starlette.responses import JSONResponse
from starlette.routing import Route

from examples.adk.a2a_consumer_agent import root_agent

# Create A2A app
a2a_app = to_a2a(root_agent, port=8001)

# Add health endpoint
async def health_check(request):
    return JSONResponse({"status": "healthy", "service": "a2a-agent"})

health_route = Route("/health", health_check, methods=["GET"])
a2a_app.routes.append(health_route)