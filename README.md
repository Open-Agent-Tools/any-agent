# Any Agent - Universal AI Agent Containerization Framework

A Python framework for automatically containerizing AI agents from any framework into standardized, protocol-compliant Docker containers.

## Overview

Take any local AI agent and automatically wrap it in a Docker container with consistent APIs. Supports A2A protocol, OpenAI-compatible endpoints, and provides a React web UI.

![any-agent-UI.png](https://raw.githubusercontent.com/Open-Agent-Tools/any-agent/main/docs/any-agent-UI.png)

## Supported Frameworks

- **Google ADK** ✅ Fully functional
- **AWS Strands** ✅ Fully functional
- **LangChain** 🔄 Detection ready
- **CrewAI** 🔄 Detection ready

## Installation

```bash
pip install any-agent-wrapper
```

## Quick Start

```bash
# Auto-detect and containerize any agent
any-agent ./my_agent/

# With specific framework (uses framework default port)
any-agent ./my_agent/ --framework adk

# With custom port override
any-agent ./my_agent/ --framework aws-strands --port 8080

# Registry deployment
any-agent ./agent/ --push registry.com/my-agent:v1.0
```

## Key Features

- **Automatic Framework Detection** - Works with Google ADK, AWS Strands, LangChain, CrewAI
- **Standardized APIs** - A2A protocol, health checks, agent discovery
- **Docker Containerization** - Optimized containers with consistent interfaces
- **React Web UI** - TypeScript + Material-UI interface for all agents
- **Multi-Protocol Support** - A2A, OpenAI-compatible endpoints

## API Endpoints

All agents expose:
- `GET /health` - Health check
- `GET /.well-known/agent-card.json` - Agent metadata
- `POST /message:send` - A2A protocol messaging
- `GET /` - React web interface

## Requirements

- Python 3.8+
- Docker
- Framework-specific dependencies as needed

## Documentation

### 📖 User Documentation
- **[User Guide](docs/user_guide.md)** - Complete usage guide with CLI reference and examples
- **[Changelog](docs/changelog.md)** - Release history and version notes

### 🔧 Developer Documentation
- **[Developer Guide](docs/developer_guide.md)** - Development setup, architecture, and contribution guide
- **[Product Requirements](PRD/README.md)** - Complete product definition and technical specifications

### 📋 Quick Navigation
- **New User?** → [User Guide](docs/user_guide.md)
- **Developer?** → [Developer Guide](docs/developer_guide.md)
- **Product Overview?** → [Product Requirements](PRD/README.md)

## Status

**Version**: 0.1.7 (Fully Functional)
**PyPI**: `pip install any-agent-wrapper`
**Test Coverage**: 381 tests passing
**Architecture**: Consolidated with <5% code duplication

Full A2A protocol compliance, comprehensive testing, and deployments across multiple frameworks.