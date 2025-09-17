# CLAUDE.md

## Critical Rules
- Type hints required (`disallow_untyped_defs = true`), 88 char line limit, Python 3.8+
- Always use UV for venv, pip, pytest, ruff, mypy
- Follow project requirements and dependencies for all development work
- **Never modify examples directory**
- **Never say "production/product ready"**

## Code Standards & Naming Conventions
- **Functions**: Use descriptive verb_noun pattern (`extract_metadata`, `validate_agent`)
- **Methods**: Avoid overly generic names (`test`, `call`, `validate` → `test_agent_functionality`, `call_agent_endpoint`, `validate_agent_structure`)
- **Variables**: Use full words over abbreviations (`description_patterns` not `desc_patterns`)
- **Classes**: Consistent noun patterns (singular vs plural) - prefer singular (`ValidationResult` not `ValidationResults`)
- **Private methods**: Clear purpose in name (`_aggregate_file_contents` → `_combine_python_files`)
- **Exception handling**: Descriptive variable names (`connection_error` not `e`)

## Project: Any Agent
Universal AI agent containerization framework. Wraps agents from any framework (ADK, Strands, LangChain) into A2A protocol-compliant Docker containers with React SPAs.

**Status**: PyPI published as `any-agent-wrapper` v0.1.7

## Architecture
3-layer: Detection & Adaptation → Protocol Layer (A2A, OpenAI, WebSocket) → Containerization
React SPA UI with Material-UI, TypeScript.

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
python -m any_agent ./agent/ --port 3081
```

## Key CLI Flags
- `-f/--framework`: Force framework (auto|adk|aws-strands|langchain|crewai)
- `--port`: Container port (default: 3080)
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


## Configuration
CLI flags, YAML files, env vars, framework configs
Sections: agent, container, protocols, monitoring

## Tools
uv, ruff, black, mypy, pytest

## UI
React SPA + TypeScript + Material-UI + Vite. A2A chat interface, responsive design.
**Note**: Use A2A clients, not curl. UI commands: `--rebuild-ui`, `python -m any_agent.ui`