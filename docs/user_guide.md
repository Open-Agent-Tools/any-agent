# User Guide: Any Agent Framework v0.1.7

## Installation

```bash
pip install any-agent-wrapper
```

## Quick Start

```bash
# Auto-detect and containerize any agent
any-agent ./my_agent/

# With specific framework and port
any-agent ./my_agent/ --framework google_adk --port 3080

# Development mode with hot reload
any-agent ./my_agent/ --localhost --port 3080
```

## CLI Reference

### Core Flags

**Framework Detection**
- `--framework TEXT`: Force framework (auto|adk|aws-strands|langchain|crewai)
- `--validate`: Validate agent structure and dependencies

**Container Management**
- `--port INTEGER`: Container port (framework defaults: ADK=8035, Strands=8045, fallback=8080)
- `--container-name TEXT`: Custom container name
- `--no-build`: Skip building container
- `--no-run`: Skip running container after building
- `--push REGISTRY_URL`: Push to container registry

**Development**
- `--localhost`: Development mode with hot reload
- `--dry-run`: Show what would be done without executing
- `--verbose`: Enable detailed logging
- `--rebuild-ui`: Force React UI rebuild
- `--no-ui`: Disable web interface

**Agent Lifecycle**
- `--remove/-r`: Remove all agent artifacts
- `--list`: Preview removable artifacts
- `--agent-name TEXT`: Unique agent identifier

## Port Configuration

Any Agent uses framework-specific default ports but allows overrides:

- **Google ADK**: Default port 8035
- **AWS Strands**: Default port 8045
- **LangChain**: Default port 8055
- **CrewAI**: Default port 8065
- **Fallback**: Default port 8080
- **Override**: Use `--port` flag to specify any port

If a port is already in use, the framework will suggest an alternative port.

## Framework Examples

### Google ADK
```bash
# Basic usage (defaults to port 8035)
any-agent ./adk_agent/ --framework adk

# With custom port
any-agent ./adk_agent/ --framework adk --port 3080

# With environment variables
GOOGLE_API_KEY=your_key any-agent ./adk_agent/
```

### AWS Strands
```bash
# Basic usage (defaults to port 8045)
any-agent ./strands_agent/ --framework aws-strands

# With custom port
any-agent ./strands_agent/ --framework aws-strands --port 8080

# With environment variables
ANTHROPIC_API_KEY=your_key any-agent ./strands_agent/
```

### LangChain/CrewAI
```bash
# Auto-detection
any-agent ./langchain_agent/
any-agent ./crewai_agent/
```

## Development Workflow

```bash
# Development with hot reload
any-agent ./my_agent/ --localhost --port 8080

# Build and push to registry
any-agent ./my_agent/ --push registry.com/my-agent:v1.0

# Agent management
any-agent ./my_agent/ --list     # Preview artifacts
any-agent ./my_agent/ --remove   # Remove artifacts
```

## Environment Variables

### Google ADK
```bash
GOOGLE_API_KEY=your_key
GOOGLE_MODEL=gemini-2.0-flash
GOOGLE_PROJECT_ID=your_project
```

### AWS Strands
```bash
ANTHROPIC_API_KEY=your_key
AWS_REGION=us-east-1
```

### Common
```bash
AGENT_PORT=8080
MCP_SERVER_URL=http://localhost:7081/mcp
```

## Configuration File

```yaml
# agent_config.yaml
agent:
  name: "My Agent"
  framework: "auto"
container:
  port: 3080
  enable_ui: true
protocols:
  a2a_enabled: true
```

```bash
any-agent ./my_agent/ --config agent_config.yaml
```

## Framework Support

| Framework | Status | A2A Support | UI Integration |
|-----------|--------|-------------|----------------|
| Google ADK | ✅ Production | Native | Chat UI |
| AWS Strands | ✅ Production | A2A Server | Chat UI |
| LangChain | 🔧 Detection | Generic Wrapper | Basic UI |
| CrewAI | 🔧 Detection | Generic Wrapper | Basic UI |

## Troubleshooting

**"No framework detected"**
- Ensure agent.py exists with framework imports
- Check agent directory structure matches framework patterns

**"Port already in use"**
- Use different port: `--port XXXX`
- Stop existing containers: `docker ps` and `docker stop <container_id>`

**"Container build failed"**
- Check framework dependencies in requirements.txt
- Verify environment variables are set correctly
- Use `--verbose` for detailed build logs

## API Endpoints

All containerized agents expose:
- `GET /health` - Health check and status
- `GET /.well-known/agent-card.json` - Agent metadata and capabilities
- `POST /message:send` - A2A protocol messaging
- `GET /` - React web interface (if UI enabled)