# CLI Usage Examples: Any Agent Framework

## Current Implementation Status ✅ Fully functional

**✅ Fully functional Frameworks:**

### Google ADK ✅ Complete
- Complete A2A protocol support with Google ADK native integration ✅
- Full JSON-RPC 2.0 A2A server with all standard methods ✅
- Agent discovery via A2A agent card specification ✅
- Session management with context IDs and conversation history ✅
- Tool execution with artifacts and metadata tracking ✅
- MCP (Model Context Protocol) integration ✅

### AWS Strands ✅ Complete  
- Unified A2A client implementation ✅
- **A2A protocol tests: PASSING (3/3)** ✅
- Anthropic Claude Sonnet 4 integration ✅
- Environment variable loading with priority order ✅
- Complete Docker containerization pipeline ✅

**✅ Infrastructure Complete:**
- Unified Docker generator supporting all frameworks ✅
- Framework detection and validation ✅  
- Environment variable priority system (CLI > agent folder > current directory) ✅
- Container registry push functionality ✅
- Helmsman service registration ✅
- React SPA UI with Material-UI and TypeScript ✅

**🔄 Framework Detection Implemented (Testing in Progress):**
- LangChain adapter completed ⚠️
- LangGraph adapter completed ⚠️  
- CrewAI adapter completed ⚠️

**🔮 Future Features - Planned:** 
- Advanced monitoring and security features ❌
- Cloud deployment automation ❌

## Universal Agent Structure (Simplified)

### Required Structure (Universal Pattern)
```
my_agent/
└── __init__.py    # REQUIRED: Must expose root_agent variable
```

### Supported Structures (All Work Identically)
```
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

# Structure 3: With subdirectories (like examples/complete_a2a/adk_test_agent/)
my_agent/
├── __init__.py     # exports root_agent
├── agent.py        # defines root_agent  
├── evals/          # optional test directory
└── docs/           # optional documentation
```

**Key Point:** Only requirement is `__init__.py` exposing `root_agent` + Google ADK imports somewhere in the directory. Any directory structure works with the same containerization approach.

## Quick Start - Most Common Commands

### Essential Working Commands (Copy-Paste Ready)

#### Direct A2A Server (Recommended for Development)

**Minimal Agent Pattern:**
```bash
# 1. Create minimal agent structure
mkdir my_agent
# my_agent/agent.py - contains your LlmAgent definition
# my_agent/__init__.py - contains: from .agent import root_agent

# 2. Start A2A server with minimal agent
uv run uvicorn my_a2a_app:a2a_app --host localhost --port 8001
```

**Using Complete Example:**
```bash
# 1. Start A2A server with full example (includes prompts, evals, etc.)
uv run uvicorn examples.complete_a2a.a2a_app:a2a_app --host localhost --port 8001

# 2. Test A2A endpoints  
curl http://localhost:8001/.well-known/agent-card.json  # Agent discovery
curl http://localhost:8001/health                        # Health check

# 3. Send A2A message via JSON-RPC
curl -X POST http://localhost:8001/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": "test-1", "method": "message/send",
    "params": {"message": {"message_id": "msg-123", "parts": [{"text": "Hello!"}], "role": "user"}}
  }'
```

#### Containerized Deployment  
```bash
# 1. Basic containerization (builds and runs by default)
python -m any_agent examples/adk_agent_only --port 8080 --helmsman

# 2. Build and run locally with Helmsman
python -m any_agent examples/complete_a2a/adk_test_agent --port 8080 --helmsman --verbose

# 3. Test what would happen (dry run)
python -m any_agent ./my_agent_directory/ --dry-run --verbose

# 4. Build and push to registry
python -m any_agent ./any_adk_agent/ --push myregistry.com/my-agent:v1.0.0

# 5. Skip building (only run existing image)
python -m any_agent ./agent/ --no-build --port 8080

# 6. Build only (don't run container)
python -m any_agent ./agent/ --no-run --port 8080
```

## A2A Client Examples ✅ Complete

### Working Python A2A Client ✅ Complete

**Location**: `examples/a2a_clients/python/a2a_client.py`

```bash
# Prerequisites: A2A server running on localhost:8035
# Start server with: uv run uvicorn examples.complete_a2a.a2a_app:a2a_app --host localhost --port 8035

# Run the A2A client example
cd examples/a2a_clients/python
python a2a_client.py

# Expected output:
# A2A Client Example
# ==================  
# Connecting to A2A server at http://localhost:8035
# Fetching agent card...
# Successfully fetched agent card: Testing_Tessie
# Initializing A2A client...
# 
# --- Sending message ---
# Sending message: Hello! Can you help me with a simple task?
# Response: (Task with complete artifacts, history, and metadata...)
```

**Features Demonstrated:**
- ✅ Modern `a2a-sdk` with ClientFactory pattern (no deprecation warnings)
- ✅ Agent card resolution from A2A server
- ✅ Complete client-server communication
- ✅ Full Task objects with conversation history
- ✅ Token usage and metadata tracking
- ✅ Proper error handling and async patterns

## Core CLI Reference

### Currently Working CLI Flags ✅ Complete
```bash
# All currently functional flags:
python -m any_agent AGENT_PATH \
  [-h/--help]                     # Show help and exit
  [--directory/-d PATH]           # Agent directory path  
  [--framework/-f {auto,adk}]     # Framework selection (only adk fully supported)
  [--port PORT]                   # Container port (default: 8080)
  [--container-name NAME]         # Custom container name
  [--no-build]                    # Skip Docker image building (default: build enabled)
  [--no-run]                      # Skip running container (default: run enabled)
  [--push REGISTRY_URL]           # Push to registry
  [--config CONFIG_FILE]          # Configuration file path (limited processing)
  [--output OUTPUT_DIR]           # Output directory
  [--protocol PROTOCOL]           # Protocol support (default: a2a)
  [--helmsman]                    # Enable Helmsman registration
  [--helmsman-url URL]            # Helmsman service URL (default: http://localhost:7080)
  [--agent-name NAME]             # Unique agent identifier for Helmsman
  [--helmsman-token TOKEN]        # Helmsman auth token
  [--verbose]                     # Verbose logging
  [--dry-run]                     # Show actions without executing
  [--remove/-r]                   # Remove all agent instances from Docker and Helmsman
  [--list]                        # List all agents that can be removed
  [--rebuild-ui]                  # Force rebuild React SPA UI
```

### UI Management Commands ✅ Complete
```bash
# Build React SPA UI only
python -m any_agent.ui build

# Check UI build status and prerequisites  
python -m any_agent.ui status

# Clean UI build artifacts and dependencies
python -m any_agent.ui clean

# Copy UI files to Docker context
python -m any_agent.ui copy ./build_context

# Get detailed UI information (JSON output available)
python -m any_agent.ui info
python -m any_agent.ui info --format json

# Force rebuild UI during agent containerization
python -m any_agent ./agent/ --rebuild-ui --port 8080
```

## Framework-Specific Usage

### Currently Implemented (Google ADK) ✅ Complete
```bash
# Auto-detect and containerize (builds and runs by default)
python -m any_agent ./adk_agent/

# Force Google ADK detection with custom port
python -m any_agent ./adk_agent/ -f adk --port 8080

# With Helmsman registration
python -m any_agent ./adk_agent/ -f adk --port 8080 --helmsman

# With custom name and Helmsman integration
python -m any_agent ./adk_agent/ -f adk --container-name my-agent --port 8080 --helmsman --agent-name my-agent-v1
```

### Planned Future Support ❌ Not Implemented
```bash
# AWS Strands agent (PLANNED)
python -m any_agent -d ./trading_agent -f aws-strands --container-name trading-bot --port 8080

# LangChain agent (PLANNED)
python -m any_agent ./langchain_agent/ -f langchain --port 5000

# CrewAI agent (PLANNED)
python -m any_agent ./crew_agent/ -f crewai --protocol openai --port 4000
```

## Development Workflow ✅ Complete

### Basic Development Commands ✅ Complete
```bash
# Standard development workflow (builds and runs by default)
python -m any_agent ./my_agent/ --port 8080

# Development with verbose output
python -m any_agent ./my_agent/ --verbose --port 8080

# Development with Helmsman integration
python -m any_agent ./my_agent/ --helmsman --verbose --port 8080

# Build only (don't run)
python -m any_agent ./my_agent/ --no-run --port 8080

# Run only (don't build - use existing image)
python -m any_agent ./my_agent/ --no-build --port 8080
```

### Testing and Validation
```bash
# Generate container files without building (dry run)
python -m any_agent ./test_agent/ --output ./generated/ --dry-run

# Validate framework detection with verbose output
python -m any_agent ./agent/ --dry-run --verbose

# Test container build without running
python -m any_agent ./agent/ --no-run --verbose
```

## Production Deployment ✅ Complete

### Registry Push Commands ✅ Complete
```bash
# Build and push to registry
python -m any_agent ./my_adk_agent/ \
  --framework adk \
  --container-name my-production-agent \
  --push myregistry.com/agents/my-agent:v1.0.0 \
  --port 8080

# Build, push, and register with Helmsman
python -m any_agent ./my_adk_agent/ \
  --framework adk \
  --container-name production-agent \
  --push myregistry.com/agents/production-agent:v1.0.0 \
  --port 8080 \
  --helmsman \
  --agent-name production-agent-v1

# Custom Helmsman URL and agent name
python -m any_agent ./my_adk_agent/ \
  --framework adk \
  --helmsman \
  --helmsman-url https://helmsman.mycompany.com \
  --agent-name my-agent-prod-001 \
  --port 8080
```

## Configuration-Driven Deployment

### Using Configuration Files
```bash
# Use YAML configuration file
python -m any_agent ./my_agent/ --config agent-config.yaml

# Override specific config values
python -m any_agent ./my_agent/ \
  --config agent-config.yaml \
  --port 9000 \
  --container-name override-name \
  --protocol a2a

# Environment-specific deployments with Helmsman registration
python -m any_agent ./agent/ \
  --config ./configs/production.yaml \
  --push myregistry.com/agent:prod \
  --helmsman \
  --agent-name financial-advisor-prod
```

**Example agent-config.yaml:**
```yaml
agent:
  name: "financial-advisor"
  description: "AI financial advisor agent"
  version: "2.1.0"
  id: "financial-advisor-prod"

container:
  port: 8080
  base_image: "python:3.11-slim"

protocols:
  - name: "a2a"
    enabled: true
    path: "/a2a"

docker:
  registry: "mycompany.azurecr.io"
  tag_format: "agents/{name}:{version}"

helmsman:
  enabled: false
  url: "https://helmsman.company.com"
  agent_id: "financial-advisor-prod"
  register_on_deploy: true
```

## Troubleshooting and Debugging

### Diagnosis Commands
```bash
# Verbose output for debugging
python -m any_agent ./problematic_agent/ \
  --framework auto \
  --verbose \
  --dry-run

# Force framework and inspect generated files
python -m any_agent ./agent/ \
  --framework adk \
  --output ./debug/ \
  --no-run \
  --verbose

# Validate agent compatibility
python -m any_agent ./agent/ \
  --dry-run \
  --verbose
```

## Agent Removal ✅ Complete

### Remove Agent Artifacts ✅ Complete
```bash
# List what can be removed
python -m any_agent ./my_agent/ --list

# Remove all agent artifacts (with confirmation)
python -m any_agent ./my_agent/ --remove

# Remove with explicit agent name
python -m any_agent ./my_agent/ --remove --agent-name MyAgent

# Remove with dry-run to see what would be removed
python -m any_agent ./my_agent/ --remove --dry-run
```

### What Gets Removed
The `--remove` flag cleans up all traces of an agent:
- ✅ **Docker containers** (running and stopped)
- ✅ **Docker images** 
- ✅ **Helmsman registrations**
- ✅ **Build contexts** (temporary directories)
- ✅ **Context tracking** (updates status log)

### Context Tracking
Each agent directory gets a `.any_agent/context.yaml` file that tracks:
- Agent metadata (name, framework, model)
- Docker artifacts (container/image IDs, names)
- Helmsman registration details
- Build and removal timestamps
- Detailed operation logs

## Help and Information

### Getting Help
```bash
# General help (both forms work)
python -m any_agent --help
python -m any_agent -h

# Show what would be detected (dry run)
python -m any_agent ./agent/ --dry-run --verbose
```

## Future Development ❌ Not Implemented

The following features are planned for future development but are not currently implemented:

### Advanced Features (Future) ❌ Not Implemented
- Multi-architecture Docker builds ❌
- Custom Dockerfile templates ❌
- Enhanced A2A protocol features and optimizations ❌
- Advanced monitoring and metrics ❌
- Rate limiting capabilities ❌
- Auto-reload for development ❌
- Batch processing of multiple agents ❌
- Kubernetes manifest generation ❌
- Cloud provider integration ❌

These examples focus on the currently working functionality while providing a foundation for future enhancements.