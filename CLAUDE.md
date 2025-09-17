# CLAUDE.md

## Critical Rules
- Type hints required (`disallow_untyped_defs = true`), 88 char line limit, Python 3.8+
- Always use UV for venv, pip, pytest, ruff, mypy
- JIRA project WOB with label "any_agent" - check for issues before starting work
- **Never modify examples directory**
- **Never say "production/product ready"**

## Project: Any Agent
Universal AI agent containerization framework. Wraps agents from any framework (ADK, Strands, LangChain) into A2A protocol-compliant Docker containers with React SPAs.

**Status**: PyPI published as `any-agent-wrapper` v0.1.7

## Architecture
3-layer: Detection & Adaptation → Protocol Layer (A2A, OpenAI, WebSocket) → Containerization
React SPA UI with Material-UI, TypeScript. Helmsman integration for agent registry.

## Quick Commands
```bash
# Setup
uv sync

# Quality checks
ruff format src/ && ruff check src/ --fix && mypy src/

# Test
pytest

# Use
python -m any_agent ./my_agent/
python -m any_agent ./agent/ --port 3081 --helmsman
```

## Key CLI Flags
- `-f/--framework`: Force framework (auto|adk|aws-strands|langchain|crewai)
- `--port`: Container port (default: 3080)
- `--helmsman`: Enable agent registry
- `--dry-run`: Preview without executing
- `--remove`: Remove deployed agents
- `--no-ui`: Disable web interface
- `--rebuild-ui`: Force React rebuild

## Framework Detection
Auto-detects by analyzing file structure, imports, and patterns. Adapters handle discovery, interface standardization, dependencies, and configuration.

## Framework Support
**✅ Fully Functional:** Google ADK, AWS Strands (A2A tests passing)
**🔄 Detection Ready:** LangChain, LangGraph, CrewAI

**Environment Variables:**
- ADK: `GOOGLE_API_KEY`, `GOOGLE_MODEL`, `MCP_SERVER_URL`
- Strands: `ANTHROPIC_API_KEY`, `AWS_REGION`

## Helmsman Integration
Agent registry/discovery. API: `localhost:7080/api`, MCP: `localhost:7081/mcp`
Env vars: `HELMSMAN_URL`, `HELMSMAN_MCP_URL`, `HELMSMAN_TOKEN`, `AGENT_ID`

## Configuration
CLI flags, YAML files, env vars, framework configs
Sections: agent, container, protocols, helmsman, monitoring

## Tools
uv, ruff, black, mypy, pytest

## UI
React SPA + TypeScript + Material-UI + Vite. A2A chat interface, responsive design.
**Note**: Use A2A clients, not curl. UI commands: `--rebuild-ui`, `python -m any_agent.ui`