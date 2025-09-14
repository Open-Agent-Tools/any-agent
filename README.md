# Any Agent - Universal AI Agent Containerization Framework

A Python framework for automatically containerizing AI agents from any framework into standardized, protocol-compliant Docker containers with consistent APIs.

This is built for the homelab crew who are working across multiple frameworks and want a clean easy interface for their agents.

## Overview

This project enables developers to take any local AI agent (regardless of underlying framework) and automatically wrap it in a Docker container with consistent, standardized API endpoints. The wrapper obfuscates and decouples users from the underlying agent implementation while exposing protocol-compliant interfaces including A2A, OpenAI-compatible APIs, and custom protocols.

![any-agent-UI.png](docs/any-agent-UI.png)

## Features

- **Framework Agnostic**: Automatically detects and adapts to different AI agent frameworks
- **Multi-Protocol Support**: Implements A2A, OpenAI-compatible, and custom protocol endpoints
- **Docker Containerization**: Generates optimized Docker containers for any agent
- **Standardized APIs**: Consistent REST endpoints regardless of underlying framework
- **Auto-Discovery**: Intelligent detection of agent entry points and patterns
- **Flexible APIs**: Support for multiple API standards and custom endpoints
- **A2A Testing Harness**: Comprehensive testing framework for A2A protocol validation and compliance
- **Working features**: Built-in monitoring, health checks, and deployment features

## Supported Frameworks

### ✅ Fully Functional
- **Google Agent Development Kit (ADK)** - Complete implementation with full testing coverage
  - Native A2A protocol support with Google ADK clients
  - MCP (Model Context Protocol) integration
  - Full end-to-end pipeline validation
  
- **AWS Strands** - Complete implementation with full testing coverage  
  - Anthropic Claude Sonnet 4 integration
  - **A2A protocol tests: PASSING (3/3)**
  - Framework-specific A2A client implementation
  - Complete Docker containerization pipeline

### 🔄 Framework Detection Implemented  
- **LangChain** - Adapter completed, integration testing in progress
- **LangGraph** - Adapter completed, integration testing in progress  
- **CrewAI** - Adapter completed, integration testing in progress

### 🔮 Future Support
- AutoGen
- Custom Python agents  
- Additional framework adapters based on community needs

## Installation

After cloning the repository:

```bash
# Run the installation script (macOS/Linux/Windows)
./install.sh

# Verify installation
any-agent --help
```

## Quick Start

```bash
# Basic usage - auto-detect and containerize
any-agent ./my_agent/

# Advanced usage with specific options  
any-agent ./super_cool_agent --framework adk --port 3081

# Production deployment with Helmsman registration
any-agent ./agent/ \
  --config prod.yaml \
  --push registry.com/my-agent:v1.0 \
  --helmsman \
  --agent-name my-agent-prod

# UI-specific commands
any-agent ./agent/ --rebuild-ui  # Force rebuild React SPA
python -m any_agent.ui build    # Build UI only

# Alternative: Module invocation (also works)
python -m any_agent ./my_agent/
```

## API Endpoints

All wrapped agents expose standardized endpoints:

**Core Endpoints:**
- `GET /health` - Health check and status
- `GET /docs` - Agent documentation and capabilities
- `GET /metrics` - Performance and usage metrics

**Protocol Endpoints:**
- `POST /message:send` - A2A protocol messaging
- `POST /v1/chat/completions` - OpenAI-compatible chat API
- `POST /invoke` - Direct agent invocation
- `WebSocket /ws` - Real-time streaming (optional)

## Architecture

The framework follows a three-layer architecture:

1. **Detection & Adaptation Layer**: Automatically detects agent frameworks and generates framework-specific adapter code
2. **Protocol Layer**: Provides multi-protocol API support (A2A, OpenAI-compatible, WebSocket, custom protocols) 
3. **Containerization Layer**: Builds optimized Docker containers with standardized endpoints

### 8-Step Pipeline Process:
1. **Port Availability Check** - Validates deployment port
2. **Framework Detection** - Automatic framework identification  
3. **Agent Validation** - Framework-specific validation
4. **Metadata Extraction** - Agent configuration and capabilities
5. **Docker Image Creation** - Unified containerization
6. **Container Startup** - Deployment with environment variables
7. **Health Check** - Container and endpoint validation
8. **End-to-End Testing** - A2A protocol and API validation

## Requirements

- Python 3.8+
- Docker
- Agent frameworks as needed

## Project Structure

```
├── src/any_agent/
│   ├── core/              # Framework detection and orchestration
│   ├── adapters/          # Framework-specific adapters (ADK, Strands, LangChain, etc.)
│   ├── api/              # FastAPI protocol implementations  
│   ├── docker/           # Container generation and Dockerfile templates
│   ├── ui/               # React SPA with TypeScript and Material-UI
│   └── testing/          # A2A testing harness and validation
├── examples/
│   ├── adk/              # Google ADK example agents
│   ├── strands/          # AWS Strands example agents
│   └── a2a_clients/      # A2A protocol client examples
├── PRD/                  # Product Requirements and Design Documents
└── docs/                 # Additional documentation
```

## Environment Configuration

The framework uses environment variables with priority order:

1. **CLI input** (highest priority) - Existing environment variables
2. **Agent folder** - `.env` file in agent directory  
3. **Current directory** - `.env` file where `any_agent` is called

### Framework-Specific Variables

**Google ADK:**
```bash
GOOGLE_API_KEY=your_key_here
GOOGLE_MODEL=gemini-2.0-flash
GOOGLE_PROJECT_ID=your_project
```

**AWS Strands:**
```bash
ANTHROPIC_API_KEY=your_key_here
AWS_REGION=us-east-1
```

**Common Variables:**
```bash
AGENT_PORT=8080
MCP_SERVER_URL=http://localhost:7081/mcp
HELMSMAN_URL=http://localhost:7080/api
```

## 🚀 Status (September 2025)

### ✅ **Fully Functional Frameworks**
- **Google ADK** - Complete implementation with enhanced Chat UI
- **AWS Strands** - Complete implementation with A2A protocol upgrade to AWS best practices  
- **100% Test Pass Rate** - All 101 automated tests + 25 manual integration tests passing
- **Zero Critical Issues** - All linting errors resolved, full type safety compliance

### 🎯 **A2A Protocol **
- **Universal A2A Support** - Single unified client works across all frameworks
- **Complete Session Isolation** - Multi-user chat sessions with zero context bleeding
- **Standards Compliance** - Full JSON-RPC 2.0 A2A protocol implementation
- **Agent Discovery** - Complete agent card endpoints for all containerized agents

### 🏗️ **Modern Architecture**
- **React SPA UI** - TypeScript + Material-UI + responsive design for all agents
- **Unified Container Pipeline** - Single Docker generator supporting multiple frameworks
- **Environment Management** - Robust priority system (CLI > agent folder > current directory)
- **Agent Lifecycle** - Complete deployment, tracking, and removal system with audit trails


## 🔮 Planned Improvements

### Upload Support
- **File Upload Integration** - Native support for document, image, and multimodal content uploads through standardized endpoints
- **Framework-Agnostic Uploads** - Automatic routing of uploaded content to appropriate framework handlers (ADK vision, Strands file processing, etc.)
- **Progress Tracking** - Real-time upload progress with resumable transfers for large files

### Universal Evaluation Framework
- **Agent Performance Validation** - Verify LLM and agent behavior meets expected performance criteria
- **Cross-Framework Benchmarking** - Standardized evaluation metrics to compare agent performance across different frameworks
- **Quality Assurance Testing** - Automated validation of agent responses, accuracy, and reliability
- **Custom Evaluation Pipelines** - Framework for domain-specific evaluation criteria and success metrics
- **Continuous Monitoring** - Real-time performance tracking and regression detection for deployed agents

### Canvas Integration
- **Visual Agent Interfaces** - Rich canvas-based interfaces for agents that work with visual content, diagrams, and interactive elements
- **Real-Time Collaboration** - Multi-user canvas sessions with agent interaction capabilities
- **Export & Integration** - Canvas content export to various formats with agent-generated annotations
- **Framework Bridge** - Seamless integration between canvas interactions and underlying agent frameworks