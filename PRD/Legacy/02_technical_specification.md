# Technical Specification: Any Agent Framework

## 1. System Architecture

### 1.1 High-Level Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                        Any Agent Framework                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  CLI Tool   │  │ React SPA   │  │  API Interface          │ │
│  │ (any-agent) │  │  Web UI     │  │  (Future)               │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                       Core Engine                              │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ Framework   │  │ Adapter     │  │ Container               │ │
│  │ Detector    │  │ Generator   │  │ Builder                 │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                     Framework Adapters                         │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ Google ADK  │  │ AWS Strands │  │ LangChain/CrewAI/etc    │ │
│  │ Adapter     │  │ Adapter     │  │ Adapters                │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Descriptions

#### Framework Detector (`src/any_agent/core/framework_detector.py:17`)
- Analyzes file structure and content to identify agent framework
- Supports multiple detection strategies per framework
- Returns framework type and confidence score

#### Localhost Orchestrator (`src/any_agent/core/localhost_orchestrator.py:21`)
- Separate pipeline for localhost development mode
- FastAPI generation via `LocalhostFastAPIGenerator`
- Hot reload and file watching capabilities
- Production UI build integration

#### Docker Orchestrator (`src/any_agent/core/docker_orchestrator.py:23`)
- Full containerization pipeline management
- Docker image generation via `UnifiedDockerfileGenerator`
- Container lifecycle management and health checks

#### Container Builder (`src/any_agent/docker/docker_generator.py:13`)
- Generates optimized Dockerfiles via `UnifiedDockerfileGenerator`
- Manages multi-stage builds with framework-specific configurations
- Handles dependency installation and UI integration

#### Context Manager (`src/any_agent/core/agent_context.py`)
- Tracks agent deployment state in `.any_agent/context.yaml`
- Stores Docker artifacts, Helmsman registrations, custom names
- Maintains lifecycle audit trail and removal logs

#### Agent Remover (`src/any_agent/core/agent_remover.py`)
- Comprehensive artifact cleanup system
- Removes Docker containers, images, build contexts
- Cleans up Helmsman registry entries
- Provides detailed success/failure reporting

## 2. Framework Detection Patterns ✅ Complete (Google ADK)

### 2.1 Google ADK Detection (Simplified) ✅ Complete
```python
# Universal Google ADK detection pattern
UNIVERSAL_DETECTION_PATTERN = {
    "required_structure": {
        "__init__.py": "Must expose root_agent variable"
    },
    "required_imports": [
        "from google.adk.agents import Agent",
        "from google.adk.agents import LlmAgent", 
        "from google.adk.a2a.utils.agent_to_a2a import to_a2a",
        "import google.adk"
    ],
    "detection_logic": "Check __init__.py for root_agent + scan all .py files for ADK imports",
    "note": "Works with any directory structure as long as __init__.py exposes root_agent"
}

# Example structures (all supported)
SUPPORTED_STRUCTURES = {
    "minimal": ["__init__.py", "agent.py"],
    "with_prompts": ["__init__.py", "agent.py", "prompts.py"], 
    "with_subdirs": ["__init__.py", "agent.py", "evals/", "docs/"],
    "a2a_reference": ["__init__.py", "a2a_app.py", "adk_test_agent/"]
}
```

### 2.2 AWS Strands Detection ✅ Complete
```python
# Detection patterns for AWS Strands  
DETECTION_PATTERNS = {
    "required_structure": {
        "agent.py": "Contains Strands agent definition with root_agent variable"
    },
    "required_imports": [
        "from strands import Agent",
        "from strands.models.anthropic import AnthropicModel",
        "import strands"
    ],
    "variables": ["root_agent = Agent(", "Agent("],
    "directory_structure": {
        "agent.py": "required - contains root_agent",
        "__init__.py": "optional - can expose root_agent",
        "prompts.py": "optional - system prompts",
        ".env": "optional - ANTHROPIC_API_KEY"
    }
}
```

## 3. A2A Protocol Implementation ✅ Complete

### 3.1 Current Implementation Status ✅ Complete

**✅ Fully Implemented A2A Protocol:**
The Google ADK A2A implementation using `google.adk.a2a.utils.agent_to_a2a.to_a2a` provides complete A2A protocol compliance including:

- `/.well-known/agent-card.json` - Agent discovery per A2A specification  
- `/health` - Health check endpoint
- `/` (POST) - Full JSON-RPC 2.0 A2A protocol server with all standard methods
- Session management with context IDs and conversation history
- Task management with artifacts and metadata tracking
- Tool execution and response handling

**✅ A2A Protocol Methods:**
- `message/send` - Send messages and receive responses
- `message/stream` - Stream responses for long-running tasks  
- `tasks/get` - Retrieve task information
- `tasks/cancel` - Cancel running tasks
- `tasks/pushNotificationConfig/*` - Manage push notification settings
- `tasks/resubscribe` - Resubscribe to task updates
- `agent/getAuthenticatedExtendedCard` - Get extended agent capabilities

**✅ Client Integration:**
Google ADK provides `RemoteA2aAgent` for programmatic access to A2A servers, enabling agent-to-agent communication.

### 3.2 Google ADK A2A Implementation

#### Simple A2A Server Setup
```python
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from starlette.responses import JSONResponse
from starlette.routing import Route

# Convert Google ADK agent to A2A server
a2a_app = to_a2a(root_agent, port=8001)

# Add custom health endpoint
async def health_check(request):
    return JSONResponse({"status": "healthy", "service": "a2a-agent"})

health_route = Route("/health", health_check, methods=["GET"])
a2a_app.routes.append(health_route)
```

#### A2A Client Integration (Modern SDK)
```python
# Modern A2A client using official a2a-sdk with ClientFactory pattern
import asyncio
import httpx
from a2a.client import ClientFactory, A2ACardResolver, ClientConfig
from a2a.client.helpers import create_text_message_object

async def connect_to_agent():
    """Example A2A client connection using modern SDK patterns"""
    base_url = "http://localhost:8035"
    
    async with httpx.AsyncClient() as httpx_client:
        # Step 1: Resolve agent card
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url
        )
        agent_card = await resolver.get_agent_card()
        
        # Step 2: Create client using ClientFactory
        client_config = ClientConfig(httpx_client=httpx_client)
        factory = ClientFactory(config=client_config)
        client = factory.create(card=agent_card)
        
        # Step 3: Send message
        message = create_text_message_object(content="Hello from A2A client!")
        
        async for response in client.send_message(message):
            print(f"Response: {response}")

# Legacy Google ADK client approach (still supported)
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH

client_agent = RemoteA2aAgent(
    name="client_agent",
    description="Client agent for A2A communication",
    agent_card=f"http://localhost:8001{AGENT_CARD_WELL_KNOWN_PATH}",
)
```

#### JSON-RPC A2A Message Format
```json
{
  "jsonrpc": "2.0",
  "id": "request-id", 
  "method": "message/send",
  "params": {
    "message": {
      "message_id": "unique-message-id",
      "parts": [{"text": "Your message content"}],
      "role": "user",
      "context_id": "optional-context-id"
    }
  }
}
```

#### A2A Response Format
```json
{
  "id": "request-id",
  "jsonrpc": "2.0",
  "result": {
    "artifacts": [{"artifactId": "...", "parts": [...]}],
    "contextId": "conversation-context-id",
    "history": [...],
    "id": "task-id",
    "kind": "task",
    "status": {"state": "completed", "timestamp": "..."},
    "metadata": {"usage": {...}}
  }
}
```

## 4. Framework Integration Patterns

### 4.1 Google ADK A2A Integration ✅ Complete

The Google ADK framework provides native A2A protocol support through built-in utilities, with **enhanced Chat UI integration as of September 2025**:

#### Recent Enhancements ✅ Fixed (September 2025)
- **Chat UI Response Extraction**: Fixed "Task completed: Task" fallback messages  
- **Context Wrapper Optimization**: ADK agents bypass unnecessary context isolation (native support)
- **Response Structure Handling**: Proper extraction from `task.status.message.parts` hierarchy
- **Framework-Specific Optimization**: ADK agents use native A2A context isolation instead of generic wrapper

#### Direct A2A Conversion
```python
from google.adk.a2a.utils.agent_to_a2a import to_a2a

# Convert any Google ADK agent to A2A-compliant server
a2a_app = to_a2a(root_agent, port=8001)
```

#### Universal ADK Agent Pattern (Simplified)
```python
# Any directory structure with these requirements:

# my_agent/__init__.py (REQUIRED)
from .agent import root_agent  # Must expose root_agent
__all__ = ["root_agent"]

# my_agent/agent.py (or any .py file with ADK imports)
from google.adk.agents import LlmAgent
root_agent = LlmAgent(name="MyAgent", ...)

# Container generation automatically handles:
# - Package structure preservation 
# - Universal import: import my_agent
# - A2A server creation: to_a2a(my_agent.root_agent)
```

#### Supported Structures (All Work Identically)
```python
# Structure 1: Minimal
my_agent/
├── __init__.py     # exports root_agent
└── agent.py        # defines root_agent

# Structure 2: With additional files  
my_agent/
├── __init__.py     # exports root_agent
├── agent.py        # defines root_agent
├── prompts.py      # optional utilities
└── requirements.txt

# Structure 3: With subdirectories
my_agent/
├── __init__.py     # exports root_agent  
├── agent.py        # defines root_agent
├── evals/          # optional test directory
└── docs/           # optional documentation

# All use same containerization approach with package preservation
```

### 4.2 AWS Strands A2A Integration ✅ Complete

AWS Strands framework integration provides comprehensive A2A protocol support with **enhanced session isolation and MCP client preservation as of September 2025**:

#### Strands-Specific Features ✅ Fully functional
- **A2AStarletteApplication Architecture**: Fully functional Starlette-based A2A server implementation
- **Agent Cards with Metadata**: Comprehensive capabilities and skills discovery
- **Enhanced Message Parsing**: Structured A2A message data extraction with messageId, taskId, contextId
- **Streaming Response Support**: Full streaming protocol compatibility
- **MCP Client Session Preservation**: Direct agent calls prevent session breakage in Docker environments
- **Context Isolation**: Thread-safe session management with proper locking mechanisms
- **Anthropic Claude Integration**: Full support for Claude Sonnet 4 models

#### Strands Agent Structure Pattern
```python
# Strands agent structure with context isolation support
my_strands_agent/
├── __init__.py          # exports root_agent  
├── agent.py             # defines Strands Agent with tools
├── requirements.txt     # strands dependencies
└── .env                 # ANTHROPIC_API_KEY

# agent.py example
from strands import Agent, tool
from strands.models.anthropic import AnthropicModel

@tool
def my_custom_tool(query: str) -> str:
    return f"Processed: {query}"

root_agent = Agent(
    model=AnthropicModel(model_id="claude-3-5-sonnet-20241022"),
    tools=[my_custom_tool],
    system_prompt="You are a helpful assistant."
)
```

#### Context Isolation Implementation
```python
# Enhanced context isolation preserving MCP client sessions
class StrandsDirectCallWrapper:
    """Wrapper that calls the original agent directly to preserve stateful connections."""
    
    def __init__(self, agent: Any):
        self.agent = agent
        self.lock = threading.RLock()
        logger.info("🔧 Using direct agent calls - MCP client sessions preserved")

    def __call__(self, message: str, context_id: Optional[str] = None, **kwargs) -> Any:
        """Process message directly through original agent (no session isolation)."""
        with self.lock:
            if context_id:
                logger.debug(f"🎯 Processing with context ID {context_id} (no isolation - preserves MCP)")
            return self.agent(message, **kwargs)
```

### 4.3 Framework Adapter Interface (Future Frameworks) ❌ Not Implemented

For frameworks without native A2A support, implement the following interface:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class FrameworkAdapter(ABC):
    """Base class for framework-specific A2A adapters"""
    
    @abstractmethod
    def detect(self, agent_path: str) -> bool:
        """Detect if framework is used in the given path"""
        pass
    
    @abstractmethod
    def generate_a2a_wrapper(self, agent_path: str) -> str:
        """Generate A2A wrapper code for the framework"""
        pass
    
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """Return required dependencies for the framework"""
        pass
    
    @abstractmethod
    def get_startup_command(self) -> str:
        """Return command to start the A2A server"""
        pass
```

#### AWS Strands Adapter ✅ Complete
```python
class AWSStrandsAdapter(FrameworkAdapter):
    def detect(self, agent_path: str) -> bool:
        # Check for Strands-specific imports and patterns
        return self._check_strands_patterns(agent_path)
    
    def generate_a2a_wrapper(self, agent_path: str) -> str:
        # Generate A2AStarletteApplication wrapper for Strands agents
        return self._create_strands_a2a_server(agent_path)
    
    def upgrade_agent_for_context_isolation(self, agent: Any) -> Any:
        # Apply context isolation wrapper preserving MCP sessions
        return upgrade_agent_for_context_isolation(agent)
```

## 5. Container Generation ✅ Complete

### 5.1 Dockerfile Template (Google ADK A2A) ✅ Complete
```dockerfile
# Optimized for A2A server deployment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables for A2A
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies including uv for faster builds
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster Python package management
RUN pip install --no-cache-dir uv

# Copy dynamically generated requirements.txt (includes detected imports)
COPY requirements.txt ./
RUN uv pip install --system --no-cache -r requirements.txt

# Copy agent package directory (preserves structure for imports)
COPY {agent_name}/ ./{agent_name}/

# Copy generated A2A entrypoint
COPY _simple_a2a_entrypoint.py .

# Set default port (configurable via environment)
ENV AGENT_PORT=8080

# Set Google ADK environment variables
ENV GOOGLE_MODEL=gemini-2.0-flash
ENV GOOGLE_API_KEY=""

# Expose configurable port
EXPOSE $AGENT_PORT

# Health check for A2A server
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$AGENT_PORT/health || exit 1

# Start A2A server using uv run uvicorn
CMD ["sh", "-c", "uv run uvicorn _simple_a2a_entrypoint:a2a_app --host 0.0.0.0 --port $AGENT_PORT"]
```

### 5.2 Dynamic Requirements Management (A2A-Focused) ✅ Complete
```python
def generate_requirements(agent_path: Path, existing_requirements: Optional[str] = None) -> str:
    """Generate requirements.txt by scanning agent code for actual imports"""
    
    # A2A baseline requirements (always needed for servers)
    a2a_base_requirements = [
        "google-adk[a2a]",      # Core A2A server support
        "a2a-sdk>=0.1.0",       # Modern client capabilities
        "uvicorn[standard]",    # A2A server runtime
        "httpx>=0.24.0",        # HTTP client for A2A communication
        "requests"              # Common utility
    ]
    
    # Scan all Python files in agent directory for imports
    detected_imports = scan_agent_imports(agent_path)
    
    # Map common import patterns to package names
    import_to_package_mapping = {
        "basic_open_agent_tools": "basic_open_agent_tools",
        "fastmcp": "fastmcp", 
        "httpx": "httpx",
        "python-dotenv": "python-dotenv",
        "dotenv": "python-dotenv",
        "pydantic": "pydantic",
        "starlette": "starlette"  # Often used with A2A apps
    }
    
    # Convert detected imports to package requirements
    agent_specific_deps = []
    for import_name in detected_imports:
        if import_name in import_to_package_mapping:
            agent_specific_deps.append(import_to_package_mapping[import_name])
    
    if existing_requirements:
        # Augment existing requirements.txt
        requirements = parse_existing_requirements(existing_requirements)
        # Ensure google-adk[a2a] (upgrade basic google-adk if needed)
        requirements = upgrade_to_a2a_requirements(requirements)
        # Add any missing detected dependencies
        requirements.extend([dep for dep in agent_specific_deps if dep not in requirements])
        requirements.extend([dep for dep in a2a_base_requirements if dep not in requirements])
    else:
        # Create new requirements with all detected dependencies
        requirements = a2a_base_requirements + agent_specific_deps
    
    return format_requirements_file(list(set(requirements)))  # Remove duplicates

def scan_agent_imports(agent_path: Path) -> Set[str]:
    """Scan all .py files in agent directory for import statements"""
    imports = set()
    
    for py_file in agent_path.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])
                        
        except Exception as e:
            logger.debug(f"Error parsing {py_file}: {e}")
            continue
            
    return imports
```

## 6. CLI Interface ✅ Complete

### 6.1 Command Structure ✅ Complete
```bash
python -m any_agent [OPTIONS] AGENT_PATH

Options:
  --framework TEXT     Force specific framework detection (auto,adk,aws-strands,langchain,crewai)
  --port INTEGER       Port for the containerized agent (default: 8080)
  --container-name TEXT  Custom name for the container
  --localhost          Enable localhost development mode (fast iteration, hot reload)
  --build             Build Docker image after generation (default: enabled)
  --run               Run container after building (default: enabled)
  --push TEXT         Push to registry (format: registry/repo:tag)
  --config FILE         Configuration file path
  --output DIR          Output directory for generated files
  --verbose             Enable verbose logging
  --helmsman            Enable Helmsman registration
  --helmsman-url TEXT   Helmsman service URL (default: http://localhost:7080/api)
  --agent-name TEXT     Unique agent identifier for Helmsman
  --helmsman-token TEXT Authentication token for Helmsman
  --remove/-r           Remove all agent artifacts
  --list                Preview artifacts that can be removed
  --help                Show help message
```

### 6.2 Configuration File Format ❌ Not Implemented
**Current Reality**: CLI accepts `--config` flag but does not process the file content.

**Documented Design** (not implemented):
```yaml
# a2a-config.yaml  
agent:
  name: "my-agent" ❌ Not processed
  description: "Custom agent description" ❌ Not processed
  version: "1.0.0" ❌ Not processed

container:
  port: 8080 ❌ Not processed
  base_image: "python:3.11-slim" ❌ Not processed
  
api:
  enable_cors: true ❌ Not processed
  rate_limit: 100 ❌ Not processed
  
framework:
  type: "auto" ❌ Not processed
  
docker:
  registry: "my-registry.com" ❌ Not processed
  tag_format: "{name}:{version}" ❌ Not processed
```

**What Actually Works**: All configuration via CLI flags only:
```bash
# All configuration must be passed as CLI flags
python -m any_agent ./agent/ \
  --port 8080 \
  --framework adk \
  --container-name my-agent \
  --helmsman --helmsman-url http://localhost:7080
```

## 7. Error Handling & Logging ✅ Complete

### 7.1 Error Categories ✅ Complete
- **Detection Errors**: Framework not detected or ambiguous
- **Adapter Errors**: Agent loading or execution failures  
- **Container Errors**: Docker build or runtime issues
- **API Errors**: Invalid requests or internal failures

### 7.2 Logging Structure ✅ Complete
```python
import structlog

logger = structlog.get_logger()

# Example usage
logger.info(
    "framework_detected",
    framework="google-adk", 
    confidence=0.95,
    agent_path="/path/to/a2a_agent.py"
)

logger.error(
    "adapter_load_failed",
    framework="google-adk",
    error=str(e),
    agent_path="/path/to/a2a_agent.py"
)
```

## 8. Key Implementation Lessons ✅ Complete

### 8.1 Google ADK A2A Integration Discoveries ✅ Complete

**✅ Use Native Google ADK A2A Utilities:**
- `google.adk.a2a.utils.agent_to_a2a.to_a2a` provides complete A2A protocol compliance
- No custom adapter layers needed - Google ADK handles all A2A message conversion internally
- Results in full JSON-RPC 2.0 server with all A2A standard methods

**✅ Dependency Management:**
- **Server (Google ADK Agents)**: Use `google-adk[a2a]` for A2A server functionality
- **Clients**: Use `a2a-sdk>=0.1.0` for modern ClientFactory pattern clients
- **Python Requirement**: Requires Python >=3.10 for a2a-sdk compatibility
- **Dual Dependencies**: Projects supporting both client and server need both packages

**✅ Development Workflow:**
- Direct uvicorn startup via `uv run uvicorn examples.complete_a2a.a2a_app:a2a_app --host localhost --port 8001`
- Faster iteration cycle than containerization for development
- Full A2A protocol testing possible via curl commands

**✅ Client-Server Architecture:**
- Server: Google ADK agent converted to A2A server via `to_a2a()`
- Client: Other agents connect via `RemoteA2aAgent` using agent card URL
- Enables true agent-to-agent communication within Google ADK ecosystem

**✅ A2A Protocol Features Validated:**
- Session management with persistent context IDs
- Conversation history maintenance across requests  
- Tool execution with structured artifacts and metadata
- Task management with completion status and timestamps
- Usage tracking with token counts and timing information

### 8.2 Critical Import Patterns

#### Minimal Required Pattern
```python
# Standard ADK agent module import pattern
from my_agent import root_agent  # Imports from __init__.py

# A2A server constants and utilities  
from google.adk.agents.remote_a2a_agent import (
    RemoteA2aAgent, 
    AGENT_CARD_WELL_KNOWN_PATH
)
```

#### Example Implementation Reference
```python
# Example from complete_a2a (includes additional files/features)
from examples.complete_a2a.adk_test_agent import root_agent

# Note: examples/complete_a2a/ contains prompts.py, evals/, requirements.txt
# These are examples of additional features, not requirements
```

### 8.3 A2A Client Implementation Validated ✅ Complete

**✅ Working Client Example**: `examples/a2a_clients/python/a2a_client.py` demonstrates:

```python
# Proven working client pattern
async with httpx.AsyncClient() as httpx_client:
    # Agent card resolution
    resolver = A2ACardResolver(httpx_client=httpx_client, base_url="http://localhost:8035")
    agent_card = await resolver.get_agent_card()
    
    # Modern client creation
    client_config = ClientConfig(httpx_client=httpx_client)
    factory = ClientFactory(config=client_config)
    client = factory.create(card=agent_card)
    
    # Message sending with complete response handling
    message = create_text_message_object(content="Hello! Can you help me with a simple task?")
    async for response in client.send_message(message):
        # Receives complete Task objects with artifacts, history, metadata
        print(response)
```

**✅ Validated Capabilities:**
- Full agent card resolution and client initialization
- Complete conversation management with context IDs
- Task artifacts with text responses and metadata
- Token usage tracking and performance metrics
- Error handling and connection management

### 8.4 Production Considerations

- **Development**: Use direct uvicorn startup for rapid testing
- **Production**: Use containerization with Helmsman registration  
- **Client Integration**: Use modern `a2a-sdk` with ClientFactory pattern
- **Health Monitoring**: Custom health endpoints can be added to Starlette routes
- **Agent Discovery**: A2A agent cards provide complete capability discovery
- **Protocol Compliance**: Google ADK ensures full A2A specification adherence

## 9. Testing Strategy ✅ Complete

### 9.1 Test Categories ✅ Complete
- **Unit Tests**: Individual component testing
- **Integration Tests**: Framework adapter testing  
- **Container Tests**: Docker build and runtime testing
- **API Tests**: A2A protocol compliance testing

### 8.2 Test Agent Structure
```
tests/
├── fixtures/
│   ├── google_adk_agent/
│   │   ├── agent.py
│   │   ├── __init__.py
│   │   └── .env
│   └── aws_strands_agent/
│       ├── agent.py  
│       └── config.yaml
├── unit/
├── integration/
└── e2e/
```

## 9. UI Architecture ✅ Complete

### 9.1 React SPA Architecture
The framework implements a modern React Single-Page Application with TypeScript and Material-UI:

#### Core Components
- **React SPA**: TypeScript-based single-page application with Vite build system
- **Material-UI v5**: Component library providing consistent design system and theming
- **UIBuildManager**: Handles React build process, prerequisites checking, and Docker integration
- **Static asset serving**: React build assets served via `/assets/` and `/static/` endpoints
- **A2A Integration**: Chat interface with real-time agent communication and session management

#### Build System Architecture
```typescript
// Vite configuration with TypeScript and Material-UI
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          mui: ['@mui/material', '@mui/icons-material'],
        },
      },
    },
  },
});
```

#### Material-UI Theme System
```typescript
// Theme configuration following PRD design system
const anyAgentTheme = createTheme({
  palette: {
    primary: {
      main: '#1f4788',  // Primary blue
      dark: '#0f2748',  // Primary blue dark
    },
    secondary: {
      main: '#1f7a4f',  // Primary green
    },
    success: { main: '#006b3c' },
    warning: { main: '#b45309' },
    error: { main: '#dc3545' },
  },
  typography: {
    fontFamily: ['-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'sans-serif'].join(','),
  },
});
```

#### Container Integration
Every containerized agent automatically includes:
- **Responsive Design**: Mobile-friendly React interface with Material-UI responsive breakpoints
- **Fixed Header/Footer**: Clean branding with "Any Agent" title and framework identification
- **Chat Interface**: A2A protocol integration with session management and message handling
- **Navigation**: Hamburger menu for API documentation and health check access
- **Error Handling**: React error boundaries with fallback UI for debugging

### 9.2 Benefits Achieved
- **Modern Stack**: Latest React patterns with TypeScript safety and Material-UI components
- **Maintainability**: Component-based architecture with single source of truth for UI logic
- **Performance**: Optimized production builds with asset caching, code splitting, and tree shaking
- **Developer Experience**: Hot reload development server, comprehensive error boundaries, and debugging tools
- **Accessibility**: WCAG 2.1 AA compliant Material-UI components with keyboard navigation
- **Responsive Design**: Mobile-first approach with Material-UI responsive breakpoints

### 9.3 Implementation Details
```python
# React SPA integration in Docker build process
def _copy_spa_files(self, build_context: Path, metadata: AgentMetadata, port: int = 8080) -> None:
    ui_manager = UIBuildManager()
    
    # Copy built React SPA files to build context
    copy_result = ui_manager.copy_dist_to_context(build_context)
    
    if not copy_result["success"]:
        # Fallback to basic HTML template if React build unavailable
        self._create_fallback_index_html(build_context, metadata, port)
    else:
        logger.info(f"Copied {copy_result['files_copied']} UI files to build context")
```

### 9.4 CLI Integration
```bash
# UI-specific build commands
python -m any_agent ./agent/ --rebuild-ui  # Force rebuild React SPA
python -m any_agent.ui build              # Build UI only
python -m any_agent.ui status             # Check UI build status
python -m any_agent.ui clean              # Clean UI build artifacts
```

## 9.5 Recent Technical Achievements ✅

### Environment Management System ✅
Implemented comprehensive environment variable management with strict priority order:

```python
class EnvironmentLoader:
    def load_env_with_priority(self, agent_path: Path, current_dir: Optional[Path] = None) -> Dict[str, str]:
        # Priority order: CLI > agent folder > current directory
        # Pipeline fails if no .env file found (no hardcoded fallbacks)
```

**Priority Order:**
1. **CLI input** (highest priority) - Existing environment variables
2. **Agent folder** - `.env` file in agent directory  
3. **Current directory** - `.env` file where `any_agent` is called

**Framework-Specific Variable Filtering:**
- Google ADK: `GOOGLE_API_KEY`, `GOOGLE_MODEL`, `GOOGLE_PROJECT_ID`
- AWS Strands: `ANTHROPIC_API_KEY`, `AWS_REGION`
- Common: `AGENT_PORT`, `MCP_SERVER_URL`, `HELMSMAN_URL`

### Unified Docker Generator ✅
Single generator supporting all frameworks through dynamic configuration:

```python
self.framework_configs = {
    "google_adk": {
        "default_port": 8080,
        "env_vars": {"GOOGLE_MODEL": "gemini-2.0-flash", "GOOGLE_API_KEY": ""},
        "dependencies": ["google-adk[a2a]", "uvicorn[standard]"],
        "entrypoint_script": "_adk_entrypoint.py",
    },
    "aws_strands": {
        "default_port": 9000,
        "env_vars": {"ANTHROPIC_API_KEY": ""},
        "dependencies": ["strands-agents[a2a]", "anthropic", "python-dotenv"],
        "entrypoint_script": "_strands_entrypoint.py",
    }
}
```

### Unified A2A Client Implementation ✅ (Architecture Simplified)
**September 2025 Update**: Simplified backend from multiple framework-specific clients to single unified implementation.

Replaced 3+ framework-specific A2A clients with single unified client using official a2a-sdk patterns:

```python
class UnifiedA2AClientHelper:
    """Single A2A client using official a2a-sdk patterns.
    
    Works consistently across all agent frameworks:
    - Google ADK, AWS Strands, LangChain, CrewAI, etc.
    """
    
    async def send_message(self, agent_url: str, message_content: str):
        # Official pattern from PRD/generic_a2a_client_design.md
        async with httpx.AsyncClient(timeout=self.timeout) as httpx_client:
            # Step 1: Create A2A client using official pattern
            client, agent_card = await self._create_a2a_client(agent_url, httpx_client)
            
            # Step 2: Create message using official helper with Role enum
            message = create_text_message_object(role=Role.user, content=message_content)
            
            # Step 3: Send message using client.send_message() - official pattern
            async for response in client.send_message(message):
                # Extract framework-agnostic responses using model_dump pattern
```

### A2A Protocol Success ✅
- **Unified Architecture**: Single client implementation using official a2a-sdk patterns
- **Google ADK**: Full A2A protocol tests passing with ClientFactory pattern
- **AWS Strands**: All A2A protocol tests passing (3/3) - agent card discovery, client connection, message exchange
- **Framework Agnostic**: Consistent behavior across all supported frameworks
- **Standards Compliant**: Official Context7 a2a-sdk patterns with proper resource management

## 10. Performance Requirements

### 10.1 Metrics & Targets
- **Detection Time**: < 1 second
- **Container Build**: < 60 seconds
- **Container Startup**: < 30 seconds  
- **API Response**: < 2 seconds (95th percentile)
- **Memory Overhead**: < 100MB additional
- **CPU Overhead**: < 10% additional

### 10.2 Optimization Strategies
- Multi-stage Docker builds
- Dependency caching
- Async/await patterns
- Connection pooling
- Response caching (where appropriate)