# Current CLI Reference: Any Agent Framework

**Last Updated**: September 1, 2025 - Post Chat UI Enhancement

## Implementation Status Summary ✅ Fully functional

### ✅ Fully Working Features ✅ Complete
- **Google ADK agent detection and containerization** - Complete with Chat UI working
- **AWS Strands agent detection and containerization** - Complete with Chat UI working
- **A2A protocol endpoint generation** (health, agent-card, execute, chat, root)
- **Docker container building and running** - Unified generator for all frameworks
- **Helmsman service registration** during deployment
- **Container registry push functionality**
- **Verbose logging and dry-run capabilities**
- **Agent lifecycle management** with context tracking
- **Complete artifact removal system** (--remove/-r flag)
- **Custom agent naming support** (--agent-name)
- **Artifact preview functionality** (--list flag)
- **Chat UI Interface** - Modern React SPA with TypeScript and Material-UI
- **A2A Session Isolation** - Framework-specific context isolation strategies

### ✅ Recently Fixed (September 2025)
- **ADK Chat UI Response Extraction** - No more "Task completed: Task" fallback messages
- **Context Wrapper Optimization** - ADK agents skip unnecessary wrapper interference
- **Enhanced Response Parsing** - Proper handling of framework-specific response structures

### ✅ Multiple Framework Support ✅ Complete
- **Google ADK** - Fully functional with native A2A context isolation
- **AWS Strands** - Fully functional with FileSessionManager isolation
- **LangChain** - Adapter completed, framework upgrade provides session isolation
- **CrewAI** - Adapter completed, framework upgrade provides session isolation

### ❌ Planned Features - Not Implemented
- Enhanced A2A protocol optimizations and advanced features
- Advanced deployment and monitoring features
- Enhanced monitoring and observability (basic health checks implemented)

## Complete CLI Reference ✅ Complete

### Command Syntax ✅ Complete
```bash
python -m any_agent AGENT_PATH [OPTIONS]
```

### Parameters

#### Required
- `AGENT_PATH` (positional): Path to agent file or directory

#### Optional Flags

##### Framework and Detection (`src/any_agent/cli.py:20-34`)
- `--directory/-d PATH`: Agent directory path (alternative to positional arg)
- `--framework/-f {auto,adk,aws-strands,langchain,crewai}`: Framework selection
  - ✅ `auto`: Auto-detection (Google ADK and AWS Strands fully functional)
  - ✅ `adk`: Force Google ADK (fully functional)
  - ✅ `aws-strands`: AWS Strands (fully functional)
  - ⚠️ `langchain`: LangChain (adapter completed, integration testing)
  - ⚠️ `crewai`: CrewAI (adapter completed, integration testing)

##### Container Configuration
- `--port INT`: Container port (default: 8080) ✅
- `--container-name TEXT`: Custom container name ✅
- `--protocol TEXT`: Protocol support (default: "a2a") ⚠️ (only a2a implemented)
- `--localhost`: Enable localhost development mode (fast iteration, hot reload) ✅

##### Build and Deploy
- `--no-build`: Skip building Docker image (default: build enabled) ✅
- `--no-run`: Skip running container after building (default: run enabled) ✅
- `--push REGISTRY_URL`: Push to registry ✅
- `--output PATH`: Output directory for generated files ✅

##### Helmsman Integration
- `--helmsman`: Enable Helmsman registration ✅
- `--helmsman-url TEXT`: Helmsman service URL (default: http://localhost:7080) ✅
- `--agent-name TEXT`: Unique agent identifier for registration ✅
- `--helmsman-token TEXT`: Authentication token for Helmsman ✅

##### Agent Lifecycle Management
- `--remove/-r`: Remove all agent artifacts (containers, images, Helmsman registrations) ✅
- `--list`: Preview all artifacts that can be removed ✅

##### Configuration and Debugging
- `--config PATH`: Configuration file path ⚠️ (accepts file, limited processing)
- `--verbose`: Enable verbose logging ✅
- `--dry-run`: Show actions without executing ✅

## Working Command Examples ✅ Complete

### 1. Basic Usage ✅ Complete
```bash
# Simplest working command
python -m any_agent examples/adk_test_agent

# With custom port
python -m any_agent examples/adk_test_agent --port 8080

# With Helmsman registration
python -m any_agent examples/adk_test_agent --helmsman --port 8080
```

### 2. Development Workflow ✅ Complete
```bash
# Build and run locally
python -m any_agent examples/adk_test_agent --build --run --port 8080

# With verbose output for debugging
python -m any_agent examples/adk_test_agent --build --run --verbose --port 8080

# Test without actually executing (dry run)
python -m any_agent examples/adk_test_agent --dry-run --verbose
```

### 3. Production Deployment ✅ Complete
```bash
# Build and push to registry
python -m any_agent examples/adk_test_agent \
  --build \
  --push myregistry.com/my-agent:v1.0.0 \
  --port 8080

# Full production pipeline with Helmsman
python -m any_agent examples/adk_test_agent \
  --framework adk \
  --container-name production-agent \
  --build \
  --push myregistry.com/agents/prod-agent:v1.0.0 \
  --port 8080 \
  --helmsman \
  --helmsman-url https://helmsman.company.com \
  --agent-name production-agent-v1 \
  --verbose
```

### 4. Agent Lifecycle Management ✅ Complete
```bash
# Preview what can be removed
python -m any_agent examples/adk_test_agent --list

# Remove all agent artifacts (with confirmation)
python -m any_agent examples/adk_test_agent --remove --verbose

# Remove agent with custom name
python -m any_agent examples/adk_test_agent --remove --agent-name my-custom-agent

# Deploy agent with custom name, then remove
python -m any_agent examples/adk_test_agent --agent-name test-agent --helmsman
python -m any_agent examples/adk_test_agent --remove  # Uses stored name automatically
```

### 5. Testing Commands ✅ Complete
```bash
# Framework detection test
python -m any_agent examples/adk_test_agent --framework auto --dry-run --verbose

# Container generation without building
python -m any_agent examples/adk_test_agent --output ./build-context --dry-run

# Registry push simulation
python -m any_agent examples/adk_test_agent --push myregistry.com/test:v1 --dry-run
```

## Generated Container Structure ✅ Complete

When successful, the framework generates:

### A2A-Compliant Endpoints ✅ Complete
- `GET /health` - Health check with A2A status
- `GET /.well-known/agent-card.json` - Agent discovery metadata
- `POST /execute` - A2A task execution
- `POST /chat` - Legacy chat compatibility  
- `GET /` - Root agent information

### Docker Assets ✅ Complete
- Dockerfile optimized for ADK agents
- A2A entrypoint script (`_a2a_entrypoint.py`)
- A2A wrapper adapter (`any_agent/adapters/a2a_wrapper.py`)
- Requirements and dependencies

### Expected Response Formats ✅ Complete
```json
# Health Check Response
{
  "status": "healthy",
  "agent_loaded": true,
  "framework": "google_adk",
  "a2a_enabled": true
}

# Agent Card Response  
{
  "name": "Testing_Tessie",
  "description": "Agent description",
  "version": "1.0.0",
  "capabilities": {
    "framework": "google_adk",
    "model": "gemini-2.0-flash"
  },
  "url": "http://localhost:8080/"
}

# Chat/Execute Response
{
  "response": "Agent response text",
  "status": "success"
}
```

## Known Limitations

### Current Issues
1. **Agent Responses**: A2A wrapper returns generic responses instead of contextual answers to user questions
2. **Framework Support**: Only Google ADK is fully implemented
3. **Protocol Support**: Only A2A protocol is implemented
4. **Configuration**: Limited YAML config file processing

### Temporary Workarounds
1. **For Testing**: Use the generated test script `./test_a2a_container.sh` for comprehensive endpoint validation
2. **For Development**: Use `--verbose --dry-run` flags to debug without building
3. **For Production**: Verify Helmsman registration manually after deployment

## Common Error Scenarios ✅ Complete

### "No framework detected" ✅ Complete
- Ensure agent.py exists with Google ADK imports
- Use `--framework adk` to force detection
- Check with `--verbose` flag for detection details

### "Port not available" ✅ Complete 
- The CLI will immediately check port availability and show helpful error messages
- Use the suggested alternative port: `--port XXXX` 
- For permission issues, use ports > 1024
- Stop existing containers with `docker ps` and `docker stop <container_id>`

### "Helmsman registration failed" ✅ Complete
- Verify Helmsman service is running on specified URL
- Check agent name uniqueness with `--agent-name` flag
- Use `--verbose` to see registration details

## Environment Variables ✅ Complete

The framework respects these environment variables:
- `HELMSMAN_URL`: Default Helmsman service URL
- `HELMSMAN_TOKEN`: Default authentication token
- `GOOGLE_API_KEY`: Required for ADK agents
- `GOOGLE_MODEL`: Model specification for ADK agents

## Development Roadmap ❌ Not Implemented

### High Priority ❌
1. **Fix A2A conversational responses**: Redesign ADK InvocationContext integration
2. **Add framework support**: Implement AWS Strands, LangChain, CrewAI adapters
3. **A2A protocol enhancements**: Advanced streaming features and optimizations

### Medium Priority ❌
4. **Enterprise features**: Advanced monitoring, security, and deployment automation
5. **Advanced features**: Monitoring, security, multi-architecture builds

### Lowest Priority - Future Development ❌
#### Cloud & Deployment Features ❌
- `--cloud PROVIDER`: Cloud provider (aws, gcp, azure) ❌ PLANNED
- `--aws-region REGION`: AWS region ❌ PLANNED  
- `--gcp-project PROJECT`: GCP project ❌ PLANNED
- `--azure-resource-group GROUP`: Azure resource group ❌ PLANNED
- `--deploy-to TARGET`: Deployment target ❌ PLANNED

*Note: Cloud deployment features are marked as lowest priority future development. Current focus is on framework support and protocol implementation.*