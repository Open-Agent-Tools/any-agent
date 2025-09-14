# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
uality requirements:
- Type hints required (`disallow_untyped_defs = true`)
- Line length limit: 88 characters
- Python 3.8+ compatibility target
- always use UV for venv, pip, pytest, ruff, mypy etc
- always use the jira project WOB with the label "any_agent" for this project
- when starting new work, check for related jira issues, if they dont exist use the @agent-user-story-crafter to create a new one, transition any work into inprogress when starting. Do not move to done without user confirmation.


## Project Overview

Any Agent is a universal AI agent containerization framework that automatically wraps AI agents from any framework (Google ADK, AWS Strands, LangChain, etc.) into standardized, A2A protocol-compliant Docker containers with modern React SPA interfaces. The system provides consistent APIs and session isolation regardless of the underlying agent implementation.

**Current Status**: Published to PyPI as `any-agent-wrapper` v0.1.1. Fully functional with Google ADK and AWS Strands frameworks, core tests passing, zero critical issues. Complete PyPI publishing pipeline with automated releases.

## Architecture

The framework follows a three-layer architecture:

1. **Detection & Adaptation Layer**: Automatically detects agent frameworks and generates framework-specific adapter code
2. **Protocol Layer**: Provides multi-protocol API support (A2A, OpenAI-compatible, WebSocket, custom protocols) 
3. **Containerization Layer**: Builds optimized Docker containers with standardized endpoints

Key components:
- **Framework Adapters**: Handle different AI agent frameworks (Google ADK, AWS Strands, etc.)
- **Protocol Handlers**: Implement various API standards and message formats
- **Unified A2A Client**: Single, framework-agnostic client with multi-turn conversation context preservation
- **Container Builder**: Generates Dockerfiles and manages container lifecycle
- **UI System**: Modern React SPA architecture with Material-UI components and TypeScript for web interfaces
- **Helmsman Integration**: Provides agent registration and discovery via Helmsman service

## Development Commands

### Setup and Installation
```bash
# Install dependencies using uv (preferred) or pip
uv sync
# or
pip install -e ".[dev]"
```

### Code Quality
```bash
# Format code (src only - tests excluded per project requirements)
ruff format src/

# Lint code (src only - tests excluded per project requirements)
ruff check src/ --fix

# Type checking
mypy src/

# Run all quality checks
ruff check src/ tests/ && black --check src/ tests/ && mypy src/
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_specific_module.py

# Run tests matching pattern
pytest -k "test_framework_detection"

# Run tests with verbose output
pytest -v
```

### CLI Usage
The main interface is through the `any_agent` module:

```bash
# Basic usage - auto-detect and containerize
python -m any_agent ./my_agent/

# Advanced usage with specific options  
python -m any_agent -d ./super_cool_agent -f adk --port 3081

# Production deployment with Helmsman registration
python -m any_agent ./agent/ \
  --config prod.yaml \
  --push registry.com/my-agent:v1.0 \
  --helmsman \
  --agent-name my-agent-prod

# UI-specific commands
python -m any_agent ./agent/ --rebuild-ui  # Force rebuild React SPA
python -m any_agent.ui build              # Build UI only
python -m any_agent.ui status             # Check UI build status
python -m any_agent.ui clean              # Clean UI build artifacts
```

### Complete CLI Reference

```
Usage: python -m any_agent [OPTIONS] AGENT_PATH

  Any Agent - Universal AI Agent Containerization Framework.

  Automatically containerize AI agents from any framework into standardized,
  protocol-compliant Docker containers with A2A protocol support.

  AGENT_PATH: Path to agent directory (Google ADK, AWS Strands, etc.)

  Examples:
    # Auto-detect and containerize any agent
    python -m any_agent ./my_agent

    # Google ADK agent with Helmsman registration   
    python -m any_agent ./adk_agent --framework adk --helmsman --agent-name my-adk-agent

    # Test mode - see what would happen   
    python -m any_agent ./my_agent --dry-run

    # Remove deployed agent   
    python -m any_agent ./my_agent --remove

Options:
  -h, --help                      Show this message and exit.
  -d, --directory DIRECTORY       Agent directory path
  -f, --framework [auto|adk|aws-strands|langchain|crewai]
                                  Force specific framework detection. Use
                                  'adk' for Google ADK agents (default: auto)
  --port INTEGER                  Port for the containerized agent (default:
                                  3080)
  --container-name TEXT           Custom name for the container
  --no-build                      Skip building Docker image (default: build
                                  enabled)
  --no-run                        Skip running container after building
                                  (default: run enabled)
  --push TEXT                     Push to registry (format: registry/repo:tag)
  --config PATH                   Configuration file path
  --output PATH                   Output directory for generated files
  --protocol TEXT                 Enable protocols
                                  (a2a,openai,websocket,custom)
  --helmsman                      Enable Helmsman agent registry integration
  --helmsman-url TEXT             Helmsman service base URL
  --agent-name TEXT               Unique agent identifier for Helmsman
                                  registry and Docker naming
  --helmsman-token TEXT           Authentication token for Helmsman
  --verbose                       Enable verbose logging
  --dry-run                       Show what would be done without executing
  -r, --remove                    Remove all instances of agent from Docker
                                  and Helmsman
  -y, --yes-to-all                Skip confirmation prompts (use with --remove
                                  for non-interactive removal)
  --list                          List all agents that can be removed
  --no-ui                         Disable web UI landing page (default: UI
                                  enabled)
  --skip-a2a-test                 Skip A2A protocol testing in end-to-end
                                  tests
  --a2a-test-timeout INTEGER      Timeout for A2A protocol tests in seconds
                                  (default: 30)
  --rebuild-ui                    Force rebuild of React SPA UI even if
                                  already built
```

## Framework Detection Patterns

The system detects agent frameworks by analyzing:
- File structure (presence of `agent.py`, `__init__.py`, config files)
- Import statements (framework-specific imports)
- Variable patterns (agent instantiation patterns)
- Directory structure conventions

Each framework adapter implements:
- **Discovery**: Detect framework-specific patterns
- **Interface**: Standardize agent invocation  
- **Dependencies**: Manage framework requirements
- **Configuration**: Handle framework-specific settings

## Framework Support Status

### ✅ Fully Functional (Complete A2A Protocol Support)
- **Google Agent Development Kit (ADK)** ✅
  - Complete implementation with enhanced Chat UI (September 2025)
  - Native A2A support with Google ADK clients
  - MCP (Model Context Protocol) integration
  - All A2A protocol tests passing
  - Located in `examples/adk/` directory
  - Environment: `GOOGLE_API_KEY`, `GOOGLE_MODEL`, `MCP_SERVER_URL`

- **AWS Strands** ✅  
  - Complete A2A protocol upgrade to AWS best practices (January 2025)
  - A2AStarletteApplication architecture with Agent Cards
  - Enhanced message parsing with structured data extraction
  - Full streaming response protocol implementation
  - Session isolation with thread-safe locking mechanisms
  - Anthropic Claude Sonnet 4 integration validated
  - **A2A protocol tests: PASSING (3/3)**
  - Located in `examples/strands/` directory
  - Environment: `ANTHROPIC_API_KEY`, `AWS_REGION`

### 🔄 Framework Detection Implemented
- **LangChain** - Adapter completed, integration testing needed
- **LangGraph** - Adapter completed, integration testing needed  
- **CrewAI** - Adapter completed, integration testing needed

All framework adapters implement standardized detection, validation, and containerization patterns with automatic A2A protocol integration.

## Helmsman Integration

Helmsman integration provides agent registration and discovery:
- **API Endpoint**: `http://localhost:7080/api` (development default)
- **MCP Endpoint**: `http://localhost:7081/mcp` (runtime communication)
- Registration happens at deployment time via CLI flags
- Runtime self-awareness through MCP client integration

Environment variables for Helmsman:
```bash
HELMSMAN_URL=http://localhost:7080/api
HELMSMAN_MCP_URL=http://localhost:7081/mcp  
HELMSMAN_TOKEN=<auth_token>
AGENT_ID=<unique_agent_identifier>
```

## Configuration Management

The framework supports multiple configuration approaches:
- CLI flags for immediate usage
- YAML configuration files for complex deployments
- Environment variables for sensitive data
- Framework-specific config file detection

Key configuration sections:
- `agent`: Basic metadata and identification
- `container`: Docker build and runtime settings
- `protocols`: API endpoint configuration (A2A, OpenAI, WebSocket)
- `helmsman`: Registration and discovery settings
- `monitoring`: Health checks, metrics, logging

## Development Environment

The codebase uses modern Python tooling:
- **uv**: Preferred dependency management and virtual environment
- **ruff**: Fast Python linter and formatter (replaces flake8, isort)
- **black**: Code formatting (consistent with ruff)
- **mypy**: Static type checking with strict configuration
- **pytest**: Testing framework with async support

## UI Architecture

The framework uses a modern React SPA architecture with TypeScript and Material-UI:

### Components
- **React SPA**: TypeScript-based single-page application with Vite build system
- **Material-UI v5**: Component library providing consistent design system
- **Build Manager**: UIBuildManager handles React build process and Docker integration
- **Static serving**: React build assets served via `/assets/` and `/static/` endpoints
- **A2A Integration**: Chat interface with multi-turn conversation context preservation and session management

### Build System
- **Vite 4.4+**: Fast build tool with TypeScript support and hot reload development
- **CLI Integration**: `--rebuild-ui` flag and dedicated `python -m any_agent.ui` commands
- **Prerequisites**: Automatic Node.js and npm version checking with helpful error messages
- **Docker Integration**: Seamless copy of build assets to container contexts

### Benefits
- **Modern**: Latest React patterns with TypeScript safety and Material-UI components
- **Maintainable**: Single source of truth for UI logic with component-based architecture
- **Performance**: Optimized production builds with asset caching and code splitting
- **Developer Experience**: Hot reload development server and comprehensive error boundaries
- **Consistent**: Unified branding ("Any Agent") across all containerized agents

### Container Integration
All containerized agents automatically include:
- **Responsive Design**: Mobile-friendly React interface with proper Material-UI theming
- **Fixed Header/Footer**: Clean branding with agent framework identification
- **Chat Interface**: A2A protocol integration with session management and message handling
- **Navigation**: Hamburger menu for API documentation and health check access
- **Error Handling**: React error boundaries with fallback UI for debugging
- curls dont work with a2a, you need to use an A2A client from a framework or a2a-sdk
- never add time estimates like "1-2 weeks"