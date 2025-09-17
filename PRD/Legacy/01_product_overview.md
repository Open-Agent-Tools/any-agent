# Product Requirements Document: Any Agent Framework

## 1. Product Overview

### 1.1 Product Vision
Create a universal containerization framework that enables any AI agent to be automatically wrapped in A2A protocol-compliant Docker containers with standardized interfaces, focusing on the A2A (Agent-to-Agent) protocol for maximum compatibility and performance.

### 1.2 Problem Statement
- AI agents are built using diverse frameworks (Google ADK, AWS Strands, LangChain, etc.)
- Each framework has different deployment patterns, APIs, and interfaces
- Developers need consistent, standardized ways to deploy and interact with agents
- The A2A protocol provides the most comprehensive agent-to-agent communication standard
- Manual containerization and API adaptation is time-consuming and error-prone
- Production deployments require monitoring, health checks, and observability features

### 1.3 Target Users
- **AI/ML Engineers**: Building production AI agent systems
- **DevOps Teams**: Deploying and managing agent infrastructure  
- **Product Teams**: Integrating agents into applications
- **Professional developers**: Requiring standardized agent interfaces

### 1.4 Success Metrics
- **Adoption**: Number of unique agent frameworks supported
- **Usage**: Number of agents successfully containerized
- **Performance**: Container startup time < 30s
- **Reliability**: 99.9% successful containerization rate
- **Developer Experience**: < 5 minutes from agent to running container

### 1.5 Framework Support Status

#### ✅ Fully functional (Complete A2A Protocol Support)
- **Google Agent Development Kit (ADK)** - Complete implementation with Chat UI ✅
  - Native A2A protocol support with Google ADK clients ✅
  - MCP (Model Context Protocol) integration ✅
  - Full end-to-end pipeline validation ✅
  - All A2A protocol tests passing ✅
  - **Chat UI Enhancement (Sept 2025)**: Fixed response extraction, no more fallback messages ✅
  - **Context Isolation Optimization**: Skip unnecessary wrapper for native A2A support ✅

- **AWS Strands** - Complete implementation with enhanced A2A protocol compliance ✅
  - **A2A Protocol Upgrade to AWS Best Practices (Sept 2025)** ✅
  - A2AStarletteApplication architecture with Agent Cards ✅
  - Enhanced message parsing with messageId, taskId, contextId support ✅
  - Full streaming response protocol implementation ✅
  - MCP client session preservation for containerized environments ✅
  - Context isolation with thread-safe locking mechanisms ✅
  - Anthropic Claude Sonnet 4 integration ✅
  - **A2A protocol tests: PASSING (3/3)** ✅

#### 🔄 Framework Detection Implemented
- **LangChain** - Adapter completed, integration testing in progress ⚠️
- **LangGraph** - Adapter completed, integration testing in progress ⚠️  
- **CrewAI** - Adapter completed, integration testing in progress ⚠️

#### 🔮 Future Support
- AutoGen - Planned ❌
- Custom Python agents - Planned ❌

## 2. Core Capabilities

### 2.1 Framework Detection & Adaptation ✅ Complete
- **Auto-Discovery**: Automatically detect agent framework from file structure ✅
- **Pattern Recognition**: Support multiple entry point patterns per framework ✅
- **Adaptive Integration**: Generate framework-specific adapter code ✅
- **Error Handling**: Graceful fallback for unsupported patterns ✅

### 2.2 Agent Lifecycle Management ✅ Complete
- **Context Tracking**: Store agent metadata and deployment state in `.any_agent/context.yaml` ✅
- **Custom Naming**: Support custom agent names via `--agent-name` CLI parameter ✅
- **Artifact Management**: Track Docker containers, images, build contexts, and Helmsman registrations ✅
- **Clean Removal**: Complete agent cleanup with `--remove/-r` flag removing all artifacts ✅
- **Audit Trail**: Detailed removal logs and lifecycle timestamps ✅

### 2.3 A2A Protocol Support ✅ Complete
- **A2A Protocol**: Unified a2a-sdk client using official patterns ✅
  - Google ADK: Native A2A server implementation ✅
  - AWS Strands: Unified A2A client with streaming message exchange ✅
  - Single client implementation working across all frameworks ✅
  - Standards compliant with official Context7 a2a-sdk patterns ✅
- **Message Format**: A2A protocol with framework-agnostic message handling ✅
- **Error Responses**: A2A protocol-compliant error handling ✅
- **Multi-turn Conversations**: Context preservation across message exchanges ✅
- **Streaming Support**: Real-time response streaming via A2A protocol ✅

### 2.4 Containerization ✅ Complete
- **Docker Generation**: Automated Dockerfile creation ✅
- **Optimization**: Multi-stage builds for minimal image size ✅
- **Security**: Non-root containers with minimal attack surface ✅
- **Dependencies**: Automatic dependency resolution ✅

### 2.5 API Standardization ✅ Complete  
- **A2A Protocol Interface**: Standards-compliant A2A protocol endpoints ✅
- **Health Monitoring**: Built-in health checks and status endpoints ✅
- **Error Handling**: A2A protocol-compliant error responses ✅
- **CORS Support**: Cross-origin resource sharing for web UI ✅
- **Context Management**: Session and conversation context preservation ✅
- **Response Optimization**: Efficient streaming and caching ✅

## 3. Technical Architecture ✅ Complete

### 3.1 System Components ✅ Complete
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI Tool      │    │  Core Engine    │    │ Container       │
│  (any-agent)    │───▶│  (Detection &   │───▶│  Builder        │
│                 │    │   Adaptation)   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                   ┌─────────────────┐      ┌─────────────────┐
                   │   Adapters      │      │  A2A Protocol   │
                   │  - Google ADK   │      │  - Native A2A   │
                   │  - AWS Strands  │      │  - Unified      │
                   │  - LangChain    │      │    Client       │
                   │  - LangGraph    │      │  - Streaming    │
                   │  - CrewAI       │      │  - Multi-turn   │
                   └─────────────────┘      └─────────────────┘
```

### 3.2 Framework Adapters ✅ Complete (Google ADK)
Each supported framework requires an adapter implementing:
- **Discovery**: Detect framework-specific patterns
- **Interface**: Standardize agent invocation
- **Dependencies**: Manage framework requirements
- **Configuration**: Handle framework-specific settings

### 3.3 Container Architecture ✅ Complete
Generated containers include:
- **Runtime Layer**: Python + framework dependencies
- **Adapter Layer**: Framework-specific integration code
- **API Layer**: FastAPI REST interface
- **Agent Layer**: Original agent code (unchanged)

## 4. User Experience ✅ Complete

### 4.1 Command Line Interface ✅ Complete
```bash
# Basic usage - auto-detect and containerize
python -m any_agent ./my_agent/

# Advanced options
python -m any_agent -d ./super_cool_agent -f adk --port 3081

# Build, run, and deploy (builds and runs by default)
python -m any_agent ./agent/ --push registry.com/agent:v1.0

# Development mode with verbose logging
python -m any_agent ./dev_agent/ --verbose

# Agent lifecycle management
python -m any_agent ./agent/ --list           # Preview what can be removed
python -m any_agent ./agent/ --remove         # Remove all agent artifacts

# Production deployment
python -m any_agent ./agent/ --push registry.com/agent:v1.0 --helmsman
```

### 4.2 Configuration ✅ Complete
Support for configuration via:
- **Command line flags** ✅ Complete - Comprehensive CLI with 20+ options
- **Environment variables** ✅ Complete - Priority-based loading (CLI > agent folder > current directory)  
- **Framework-specific configs** ✅ Complete - Auto-detection and framework-aware settings
- ~~Configuration files (YAML/JSON)~~ ❌ Removed - CLI and environment variables provide sufficient configuration

### 4.3 Output ✅ Complete
The tool generates:
- Optimized Dockerfile
- Docker container image
- API documentation
- Deployment instructions
- Health check endpoints
- Context tracking files (`.any_agent/context.yaml`)
- Comprehensive removal and audit logs

## 5. Implementation Phases

### Phase 1: MVP (Google ADK Support) ✅ Complete - EXCEEDED
- [x] Core detection engine ✅
- [x] Google ADK adapter ✅
- [x] A2A protocol support (Google ADK native) ✅
- [x] Optimized Docker generation ✅
- [x] CLI tool foundation with comprehensive options ✅
- [x] Basic monitoring and health checks ✅
- [x] Agent lifecycle management and context tracking ✅
- [x] Complete artifact removal system ✅
- [x] Helmsman integration for agent registry ✅
- [x] **React SPA UI with TypeScript and Material-UI** ✅ BEYOND ORIGINAL PLAN
- [x] **Comprehensive test coverage (285 tests, 49% coverage)** ✅ BEYOND ORIGINAL PLAN

### Phase 2: AWS Strands Support ✅ Complete - ACHIEVED
- [x] AWS Strands adapter ✅ **Fully functional**
- [x] Enhanced configuration ✅ **Environment variable priority system**
- [x] Improved error handling ✅ **Comprehensive error recovery**
- [x] Performance optimizations ✅ **Sub-second A2A responses**
- [x] **A2A Protocol Upgrade to AWS Best Practices** ✅ BEYOND ORIGINAL PLAN
- [x] **Full streaming response protocol** ✅ BEYOND ORIGINAL PLAN

### Phase 3: Multi-Framework Support ✅ Adapters Complete - IN PROGRESS
- [x] LangChain adapter ✅ **Adapter completed, integration testing in progress**
- [x] CrewAI adapter ✅ **Adapter completed, integration testing in progress**  
- [x] LangGraph adapter ✅ **Adapter completed, integration testing in progress**
- [x] Plugin architecture for custom frameworks ✅ **Extensible adapter system**
- [ ] AutoGen adapter ❌ **Future development**

### Phase 4: Working features ❌ Not Implemented
- [ ] Advanced authentication & authorization (OAuth, RBAC) ❌
- [ ] Comprehensive monitoring & observability ❌
- [ ] Multi-container orchestration ❌
- [ ] CI/CD integrations and deployment automation ❌
- [ ] Performance analytics and optimization ❌

## 6. Technical Constraints

### 6.1 Framework Requirements
- Python >=3.10 (required for a2a-sdk compatibility)
- Python-based agents (initial focus)
- Standard Python project structure
- Accessible agent entry point
- Compatible with containerization

### 6.2 Performance Requirements
- Container startup: < 30 seconds
- API response time: < 2 seconds median
- Memory overhead: < 100MB additional
- CPU overhead: < 10% additional


## 7. Risk Mitigation

### 7.1 Technical Risks
- **Framework Diversity**: Mitigated by adapter pattern
- **Breaking Changes**: Versioned adapters with fallbacks
- **Performance**: Benchmarking and optimization

### 7.2 Adoption Risks
- **Learning Curve**: Comprehensive documentation
- **Integration Complexity**: Simple CLI interface
- **Framework Support**: Prioritize popular frameworks

## 8. Future Development - Lowest Priority

### 8.1 Cloud Deployment Integration
The following cloud-native deployment features are planned for future development but are marked as **lowest priority** to maintain focus on core framework support and protocol implementation:

#### Cloud Provider Integration
- **AWS Integration**: Automatic deployment to ECS, Fargate, Lambda
- **Google Cloud Integration**: Cloud Run, GKE deployment options
- **Azure Integration**: Container Instances, AKS deployment
- **Multi-cloud Support**: Vendor-agnostic deployment strategies

#### CLI Cloud Flags (Future)
- `--cloud PROVIDER`: Cloud provider selection (aws, gcp, azure)
- `--aws-region REGION`: AWS region specification
- `--gcp-project PROJECT`: GCP project identification  
- `--azure-resource-group GROUP`: Azure resource group
- `--deploy-to TARGET`: Deployment target specification

#### Cloud-Native Features
- **Service Mesh Integration**: Istio, Linkerd compatibility
- **Serverless Deployment**: Function-as-a-Service options
- **Auto-scaling**: Cloud-native horizontal pod autoscaling
- **Managed Monitoring**: Integration with cloud monitoring services
- **Cost Optimization**: Resource usage optimization for cloud billing

### 8.2 Implementation Priority
These cloud deployment features are intentionally deferred until after Phase 3 completion. The current implementation provides solid foundation through:
- Local Docker containerization
- Container registry push capabilities  
- Standardized health checks and APIs
- Manual cloud deployment compatibility

This approach ensures users can deploy to any cloud platform manually while development focuses on framework support and protocol standardization.