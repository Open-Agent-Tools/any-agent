# Technical Specification: Any Agent Framework v0.2.0

## System Architecture

### 3-Layer Design
1. **CLI & Web UI Layer** - CLI tool, React SPA, A2A client integration
2. **Core Engine** - Framework detection, configurable adapters, orchestrators
3. **Shared Module Layer** - URL builder, context manager, UI routes, templates

### Key Components

**Framework Detection**
- Pattern-based detection with confidence scoring
- Support for Google ADK, AWS Strands, LangChain, CrewAI
- Configurable adapter system with 95% code reduction

**Orchestration**
- **Docker Pipeline** - Container generation, health checks, deployment
- **Localhost Pipeline** - Hot reload development with file watching

**Context Management**
- Thread-safe session isolation for multi-user scenarios
- Framework-specific strategies (native, session-managed, instance copying)

## CLI Interface

```bash
# Core functionality
python -m any_agent ./my_agent/ --port 3080
python -m any_agent ./agent/ --framework google_adk
python -m any_agent ./agent/ --localhost --rebuild-ui
```

## API Protocols

### A2A Protocol Endpoints
- `POST /message:send` - Agent-to-agent messaging
- `GET /health` - Health and status checks
- `GET /.well-known/agent-card.json` - Agent discovery metadata

### Framework Support
- **Google ADK** - Native A2A with `to_a2a()` utilities
- **AWS Strands** - A2A server with `A2AStarletteApplication`
- **LangChain/CrewAI** - Generic A2A wrapper with FastAPI

## Environment Configuration

```bash
# Google ADK
GOOGLE_API_KEY=<key>
GOOGLE_MODEL=gemini-2.0-flash

# AWS Strands
ANTHROPIC_API_KEY=<key>
AWS_REGION=us-east-1

# Common
AGENT_PORT=8080
MCP_SERVER_URL=<url>
```

## Container Architecture

### Dockerfile Generation
- Multi-stage builds with optimized base images
- Framework-specific dependency installation
- Health check and startup validation
- Environment variable injection

### Context Isolation
- **Google ADK** - Native context support, isolation skipped
- **AWS Strands** - Session-managed with MCP client preservation
- **LangChain/CrewAI** - Instance copying with comprehensive attribute preservation

## Quality Assurance

- **338 automated tests** across all modules
- **Zero circular dependencies** with architectural validation
- **Performance targets** - <30s startup, <10ms context creation
- **Code quality** - <5% duplication, full type safety

## Deployment Targets

- **Development** - Localhost with hot reload and UI dev server
- **Production** - Docker containers with health checks and monitoring
- **Registry** - Container push with tagging and versioning

## Framework Roadmap

**High Priority** - Performance optimization, Microsoft Semantic Kernel
**Medium Priority** - Haystack framework, custom plugin system