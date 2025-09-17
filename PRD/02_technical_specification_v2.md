# Technical Specification: Any Agent Framework v0.1.7

## 1. System Architecture

### 1.1 High-Level Architecture (Updated)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Any Agent Framework                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────────┐ │
│  │  CLI Tool   │  │ React SPA   │  │ A2A Client  │  │ Helmsman      │ │
│  │ (any-agent) │  │  Web UI     │  │ Integration │  │ Registry      │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────────┘ │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                        Core Engine (Consolidated)                      │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────────┐ │
│  │ Framework   │  │ Configurable│  │ Localhost   │  │ Docker        │ │
│  │ Detection   │  │ Adapters    │  │ Orchestrator│  │ Orchestrator  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────────┘ │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                     Shared Module Layer (New)                          │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────────┐ │
│  │ URL Builder │  │ Context     │  │ Unified UI  │  │ Template      │ │
│  │ (URLs)      │  │ Manager     │  │ Routes      │  │ Generator     │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────────┘ │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                      Framework Adapters                                │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────────┐ │
│  │ Google ADK  │  │ AWS Strands │  │ LangChain   │  │ CrewAI        │ │
│  │ (Native A2A)│  │ (A2A+Ctx)   │  │ (Generic)   │  │ (Generic)     │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Descriptions

#### Core Engine Components

##### Framework Detection (`src/any_agent/core/framework_detector.py`)
- **Multi-strategy detection** with confidence scoring
- **Pattern matching** on imports, file structure, and content
- **Configurable adapters** with unified interface
- **Auto-detection** with manual override support

##### Configurable Adapters (`src/any_agent/adapters/`)
- **Unified base classes** eliminate code duplication
- **95% reduction** in adapter code through configuration approach
- **Metadata extraction** for agent name, model, instructions
- **Validation system** with detailed error reporting

##### Orchestrators
- **Localhost Orchestrator** (`src/any_agent/core/localhost_orchestrator.py`)
  - Development-focused pipeline with hot reload
  - Localhost-specific URL generation and routing
  - UI dev server integration with proxy

- **Docker Orchestrator** (`src/any_agent/core/docker_orchestrator.py`)
  - Production containerization pipeline
  - Health check validation and startup verification
  - Container registry integration

#### Shared Module Layer (New Architecture)

##### URL Builder (`src/any_agent/shared/url_builder.py`)
- **ConsolidatedURLBuilder** eliminates URL duplication
- **Deployment-aware** (Docker vs localhost) URL construction
- **Environment variable integration** with fallbacks
- **Used by:** Chat endpoints, templates, orchestrators

##### Context Manager (`src/any_agent/core/context_manager.py`)
- **Unified context isolation** for A2A protocol compliance
- **Thread-safe state management** with context statistics
- **BaseContextWrapper** abstract base with specialized implementations
- **SessionManagedWrapper** for frameworks with built-in session support
- **GenericContextWrapper** with agent instance copying

##### Unified UI Routes (`src/any_agent/shared/unified_ui_routes.py`)
- **Strategy pattern** abstracts FastAPI vs Starlette differences
- **Framework-aware routing** (ADK/Strands use Starlette for A2A compatibility)
- **Deployment-specific templates** (Docker vs localhost static serving)
- **Eliminates UI route duplication** across framework generators

##### Template Generator (`src/any_agent/shared/entrypoint_templates.py`)
- **Framework-specific entrypoint generation** with context isolation
- **Chat endpoint integration** for web UI compatibility
- **Working directory management** for relative import resolution
- **Environment variable templating**

#### Framework Adapters

##### Google ADK Adapter (`src/any_agent/adapters/google_adk_adapter.py`)
- **Native A2A support** - no context wrapper needed
- **Comprehensive metadata extraction** with variable pattern matching
- **Relative import resolution** for containerization
- **Root agent validation** via __init__.py analysis

##### AWS Strands Adapter (`src/any_agent/adapters/aws_strands_adapter.py`)
- **A2A + Context isolation** via specialized executor
- **Built-in session management** integration
- **MCP client preservation** during context switching
- **Streaming response support**

##### Generic Adapters (LangChain, CrewAI, etc.)
- **Agent instance copying** for context isolation
- **Attribute preservation** during agent duplication
- **Fallback mechanisms** for unsupported patterns
- **Configurable approach** reduces code duplication

### 1.3 A2A Protocol Integration

#### Native A2A Frameworks
- **Google ADK**: Direct `to_a2a()` utility usage
- **AWS Strands**: A2AStarletteApplication with context executor

#### Generic Framework A2A Wrapping
- **Context isolation wrapper** prevents session bleeding
- **Agent card generation** with capability detection
- **Message routing** through unified A2A interface
- **Error handling** with graceful fallbacks

#### A2A Client Integration
- **UnifiedA2AClientHelper** (`src/any_agent/api/unified_a2a_client_helper.py`)
- **Chat session management** via web UI
- **Task cancellation** and cleanup support
- **Multi-framework client abstraction**

### 1.4 Deployment Architectures

#### Localhost Development
```
Agent Code → Framework Detection → Adapter → Localhost Entrypoint
                                              ↓
                                         uvicorn server
                                              ↓
                                   http://localhost:PORT
                                              ↓
                                    [Optional UI Dev Server]
```

#### Docker Production
```
Agent Code → Framework Detection → Adapter → Docker Entrypoint + Dockerfile
                                              ↓
                                         Docker Build
                                              ↓
                                       Container Image
                                              ↓
                                         Production Deploy
```

#### Helmsman Registry Integration
```
Agent Container → Agent Card Generation → Registry Registration
                                           ↓
                                  Helmsman Discovery API
                                           ↓
                                    Agent Marketplace
```

### 1.5 Quality and Performance

#### Code Quality Improvements
- **30% → <5% code duplication** across shared modules
- **Zero circular dependencies** validated by boundary checker
- **338 tests passing** with 43 new consolidated system tests
- **Comprehensive error handling** with detailed validation

#### Performance Characteristics
- **Container startup**: < 30 seconds (validated)
- **Memory footprint**: Minimal overhead from consolidated modules
- **Context switching**: Thread-safe with RLock protection
- **URL generation**: Cached builders for performance

#### Reliability Features
- **Health check endpoints** on all generated containers
- **Graceful error handling** with fallback behaviors
- **Context cleanup** prevents memory leaks
- **Backward compatibility** maintained for all existing interfaces

## 2. Protocol Support Matrix

| Framework | A2A Support | Context Isolation | UI Integration | Status |
|-----------|-------------|-------------------|----------------|--------|
| Google ADK | ✅ Native | ✅ Built-in | ✅ Starlette | Production |
| AWS Strands | ✅ A2AStarlette | ✅ Session Mgmt | ✅ Starlette | Production |
| LangChain | ✅ Generic | ✅ Instance Copy | ✅ FastAPI | Detection Ready |
| CrewAI | ✅ Generic | ✅ Instance Copy | ✅ FastAPI | Detection Ready |
| Custom | ✅ Generic | ✅ Instance Copy | ✅ Auto-Select | Extensible |

## 3. API Interfaces

### 3.1 CLI Interface
```bash
# Core functionality
python -m any_agent ./my_agent/ --port 3080
python -m any_agent ./agent/ --helmsman --rebuild-ui

# Framework override
python -m any_agent ./agent/ --framework google_adk
python -m any_agent ./agent/ --framework aws-strands --dry-run

# Development modes
python -m any_agent ./agent/ --localhost --port 8080
python -m any_agent ./agent/ --remove
```

### 3.2 Generated Container Endpoints

#### Standard A2A Endpoints
- `POST /message:send` - A2A message sending
- `GET /.well-known/agent-card.json` - Agent capability card
- `GET /health` - Container health check
- `GET /describe` - Agent description (UI fallback)

#### Web UI Integration (Optional)
- `POST /chat/create-session` - Create chat session
- `POST /chat/send-message` - Send chat message
- `POST /chat/cleanup-session` - Cleanup session
- `POST /chat/cancel-task` - Cancel running task
- `GET /` - Serve React SPA UI

### 3.3 Configuration Interface

#### Environment Variables
```bash
# Framework-specific
GOOGLE_API_KEY=<key>           # Google ADK agents
ANTHROPIC_API_KEY=<key>        # AWS Strands agents
AGENT_PORT=8080                # Container port
MCP_SERVER_URL=<url>           # MCP server connection

# Helmsman integration
HELMSMAN_URL=<url>             # Registry API endpoint
HELMSMAN_TOKEN=<token>         # Authentication token
AGENT_ID=<id>                  # Unique agent identifier
```

#### YAML Configuration (Optional)
```yaml
agent:
  name: "My Agent"
  framework: "auto"  # auto, google_adk, aws-strands, etc.

container:
  port: 3080
  enable_ui: true
  health_check: true

protocols:
  a2a_enabled: true
  openai_compatible: false

helmsman:
  register: true
  url: "http://localhost:7080"
```

## 4. Architecture Decisions

### 4.1 Consolidated Shared Modules
**Decision**: Create unified modules for URL construction, context management, and UI routes.

**Rationale**:
- Eliminates 30% code duplication across framework adapters
- Provides consistent behavior across deployment types
- Simplifies maintenance and testing
- Enables architectural boundary validation

**Implementation**:
- `url_builder.py` - Consolidated URL construction
- `context_manager.py` - Unified context isolation
- `unified_ui_routes.py` - Framework-agnostic UI routing
- `module_boundaries.py` - Architectural validation

### 4.2 Configurable Adapter Pattern
**Decision**: Replace pattern-based adapters with configuration-driven approach.

**Rationale**:
- 95% reduction in adapter code duplication
- Consistent metadata extraction across frameworks
- Easier to add new framework support
- Better error handling and validation

**Implementation**:
- `ConfigurableFrameworkAdapter` base class
- Framework-specific configurations with validation rules
- Unified metadata extraction and validation

### 4.3 Context Isolation Strategy
**Decision**: Framework-aware context management with specialized wrappers.

**Rationale**:
- A2A protocol requires session isolation
- Different frameworks need different isolation strategies
- Preserve performance and connection reuse where possible
- Maintain backward compatibility

**Implementation**:
- Session-managed wrappers for frameworks with built-in session support
- Instance copying for generic frameworks
- Thread-safe context state management
- Statistics and cleanup capabilities

### 4.4 Layered Module Architecture
**Decision**: Clear module boundaries with dependency validation.

**Rationale**:
- Prevents circular dependencies
- Enables independent testing and development
- Documents system responsibilities
- Supports incremental refactoring

**Implementation**:
- Foundation layer (url_utils, basic utilities)
- Consolidation layer (url_builder, context_manager)
- Specialization layer (framework-specific modules)
- Orchestration layer (template generators, orchestrators)

## 5. Future Considerations

### 5.1 Planned Enhancements
- **OpenAI-compatible endpoint generation** for broader integration
- **Kubernetes deployment manifests** for cloud-native deployments
- **Monitoring and observability** integration (Prometheus/Grafana)
- **Multi-agent orchestration** capabilities

### 5.2 Framework Roadmap
- **Microsoft Semantic Kernel** adapter development
- **Haystack framework** support
- **Custom framework** plugin system
- **Performance optimization** for high-throughput scenarios

### 5.3 Scalability Considerations
- **Horizontal scaling** with load balancer support
- **Database integration** for persistent context storage
- **Multi-region deployment** capabilities
- **Agent marketplace** integration beyond Helmsman