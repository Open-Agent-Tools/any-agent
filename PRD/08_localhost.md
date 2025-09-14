# Localhost Development Experience PRD

## Status: ✅ Complete - Fully functional

**Problem Solved**: Localhost and Docker modes now have **identical A2A APIs** with 1:1 parity.

**Solution Delivered**: `--localhost` flag provides the exact same A2A protocol architecture as Docker, with only the target host being different.

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Proposed Solution](#2-proposed-solution)
3. [Technical Architecture](#3-technical-architecture)
4. [CLI Interface Design](#4-cli-interface-design)
5. [Development Workflow](#5-development-workflow)
6. [Implementation Plan](#6-implementation-plan)
7. [Success Metrics](#7-success-metrics)

## 1. Problem Statement

### 1.1 Current Development Pain Points

#### Slow Docker Iteration Cycle
- Docker build + container startup: 30-60 seconds per change
- Image layer rebuilds for code changes
- Container lifecycle management overhead
- No hot reload capabilities

#### Complex Manual Setup
- Requires deep framework knowledge (uvicorn, A2A protocol)
- Manual API endpoint creation
- Manual UI integration
- No standardized local development patterns

#### Missing Development Features
- No file watching / hot reload
- Limited debugging capabilities
- No localhost-optimized error handling
- Inconsistent local vs production experience

### 1.2 Developer Personas Affected

- **AI Agent Developers**: Need fast iteration on agent logic
- **Frontend Developers**: Building UIs that integrate with agents
- **QA Engineers**: Testing agent behavior locally
- **DevOps Engineers**: Validating deployment configs

## 2. Proposed Solution

### 2.1 Localhost Pipeline Overview

Add `--localhost` flag that runs the full Any Agent pipeline locally:

```bash
# New localhost option
python -m any_agent ./my_agent/ --localhost --port 8080

# Equivalent to Docker pipeline but served locally:
# 1. Framework detection ✓
# 2. Agent validation ✓  
# 3. API generation ✓
# 4. UI integration ✓
# 5. Serve via uvicorn (instead of Docker)
```

### 2.2 API Consistency Achievement ✅

**Problem**: Localhost and Docker had different APIs, breaking the "only target host different" principle.

**Solution**: Unified architecture ensures 1:1 API parity between modes.

| Component | Docker Mode | Localhost Mode | Status |
|-----------|-------------|----------------|--------|
| **AWS Strands** | A2AServer + ContextAwareStrandsA2AExecutor | A2AServer + ContextAwareStrandsA2AExecutor | ✅ **Identical** |
| **Google ADK** | to_a2a(root_agent) | to_a2a(root_agent) | ✅ **Identical** |
| **Agent Loading** | Real root_agent integration | Real root_agent integration | ✅ **Fixed** |
| **Context Isolation** | upgrade_agent_for_context_isolation() | upgrade_agent_for_context_isolation() | ✅ **Identical** |
| **Endpoints** | Standard A2A protocol | Standard A2A protocol | ✅ **Fixed** |
| **Dependencies** | strands-agents[a2a], a2a-sdk | strands-agents[a2a], a2a-sdk | ✅ **Identical** |

### 2.3 Feature Parity Status ✅

| Feature | Docker Pipeline | Localhost Pipeline |
|---------|----------------|-------------------|
| Framework Detection | ✅ | ✅ **Complete** |
| A2A Protocol Support | ✅ | ✅ **Complete** |
| React SPA UI | ✅ | ✅ **Complete** |
| Health Endpoints | ✅ | ✅ **Complete** |
| Helmsman Integration | ✅ | ✅ **Complete** |
| Hot Reload | ❌ | ✅ **Complete** |
| Fast Startup | ❌ | ✅ **Complete** |

## 3. Technical Architecture

### 3.1 Pipeline Divergence Point (`src/any_agent/cli.py:368`)

**Actual Implementation**: CLI entry point after argument validation

```python
# Current implementation (src/any_agent/cli.py:368)
if localhost:
    click.echo("🏠 Any Agent Framework - Localhost Development Mode")
    localhost_orchestrator = LocalhostOrchestrator()  # Separate orchestrator
    result = localhost_orchestrator.deploy_agent_localhost(...)
else:
    click.echo("🚀 Any Agent Framework - MVP Pipeline") 
    orchestrator = AgentOrchestrator()  # Docker pipeline
    results = orchestrator.run_full_pipeline(...)
```

### 3.2 Separate Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Entry Point                         │
│                     (Shared Validation)                         │
└─────────────────────┬───────────────────┬─────────────────────┘
                      │                   │
         ┌────────────▼──────────┐ ┌──────▼───────────────┐
         │   Docker Pipeline     │ │  Localhost Pipeline  │
         │   (Existing)          │ │  (New - Separate)    │
         │                       │ │                      │
         │ AgentOrchestrator     │ │ LocalhostOrchestrator│
         │ ├─ Framework Detection│ │ ├─ Framework Detection│
         │ ├─ Docker Generation  │ │ ├─ FastAPI Generation │
         │ ├─ Container Build    │ │ ├─ Uvicorn Server     │
         │ └─ Container Run      │ │ ├─ File Watcher      │
         │                       │ │ └─ Hot Reload        │
         └───────────────────────┘ └──────────────────────┘
```

### 3.3 Shared Components (No Duplication)

Both pipelines reuse these existing components:
- **Framework Detection**: `FrameworkDetector` class
- **Agent Validation**: Framework adapters validation methods
- **Metadata Extraction**: `extract_metadata()` from adapters
- **Environment Loading**: `EnvironmentLoader` class
- **Port Management**: `PortChecker` class

### 3.4 Localhost-Specific Components

#### LocalhostOrchestrator Class
```python
class LocalhostOrchestrator:
    """Separate orchestrator for localhost development mode."""
    
    def __init__(self):
        # Reuse existing components
        self.framework_detector = FrameworkDetector()
        self.env_loader = EnvironmentLoader() 
        self.port_checker = PortChecker()
        
        # Localhost-specific components
        self.fastapi_generator = LocalhostFastAPIGenerator()
        self.file_watcher = AgentFileWatcher()
        self.localhost_server = LocalhostServer()
    
    def run_localhost_pipeline(self, agent_path: str, port: int) -> Dict[str, Any]:
        # 1. Framework detection (reuse existing)
        # 2. Agent validation (reuse existing)
        # 3. Generate FastAPI app (localhost-specific)
        # 4. Start uvicorn with hot reload (localhost-specific)
        # 5. Setup file watching (localhost-specific)
```

#### LocalhostServer Class
```python
class LocalhostServer:
    """Uvicorn-based local development server."""
    
    async def start_with_hot_reload(self, app, agent_path: Path, port: int):
        # Start uvicorn server with reload capabilities
        # Integrate with file watcher for automatic restarts
```

#### File Watcher Integration
```python
class AgentFileWatcher:
    """Watches agent files and triggers server restart."""
    
    def watch_agent_directory(self, agent_path: Path):
        # Watch .py files, .env files, requirements.txt
        # Trigger graceful server restart on changes
```

## 4. CLI Interface Design

### 4.1 New Localhost Flag

```bash
python -m any_agent AGENT_PATH --localhost [OPTIONS]

New Localhost Options:
  --localhost                Enable localhost development mode
  --hot-reload              Enable file watching and auto-restart (default: true)
  --dev-ui                  Use React dev server with HMR (default: true)  
  --localhost-only          Bind to 127.0.0.1 instead of 0.0.0.0
```

### 4.2 Command Examples

#### Basic Localhost Development
```bash
# Fast local development with hot reload
python -m any_agent ./my_agent/ --localhost --port 8080

# Output:
# 🔍 Framework detected: google-adk  
# 🏗️  Generating localhost server...
# 🌐 React dev server starting...
# 🚀 Localhost server ready!
#     Agent: http://localhost:8080/
#     UI: http://localhost:3000/ (dev server)
#     Health: http://localhost:8080/health
# 👀 Watching for file changes...
```

#### Production-Like Local Testing
```bash
# Test production config locally (no hot reload)
python -m any_agent ./my_agent/ --localhost --no-hot-reload --port 8080

# With Helmsman integration
python -m any_agent ./my_agent/ --localhost --helmsman --port 8080
```

### 4.3 Error Handling

#### Port Conflicts
```bash
# Intelligent port suggestion
$ python -m any_agent ./agent/ --localhost --port 8080
❌ Port 8080 is busy (process: docker-proxy)
💡 Suggestion: Try --port 8081 (available)
```

#### Agent Validation Errors
```bash
# Clear localhost-optimized error messages
$ python -m any_agent ./broken_agent/ --localhost  
❌ Localhost validation failed:
   • No 'root_agent' found in __init__.py
   • Missing required import: from google.adk.agents import Agent
   
💡 Fix suggestions:
   1. Add to __init__.py: from .agent import root_agent
   2. Install: pip install google-adk[a2a]
```

## 5. Development Workflow

### 5.1 Typical Developer Journey

#### Phase 1: Initial Setup (10 seconds)
```bash
python -m any_agent ./my_agent/ --localhost --port 8080
# Server starts, UI launches, ready to develop
```

#### Phase 2: Iterative Development (2-3 seconds per change)
1. Edit agent code in IDE
2. File watcher detects change
3. Server automatically restarts
4. Browser refreshes with new behavior

#### Phase 3: Integration Testing
```bash
# Test A2A protocol compliance
curl http://localhost:8080/.well-known/agent-card.json

# Test chat functionality
# Visit http://localhost:3000/ for interactive UI testing
```

### 5.2 Hot Reload Capabilities

#### Files Watched
- `*.py` files (agent logic)
- `.env` files (environment variables)
- `requirements.txt` (dependencies)
- `prompts.py` (agent prompts)

#### Restart Triggers
- Python file changes: Full server restart
- .env changes: Environment reload + restart
- UI file changes: HMR via React dev server

### 5.3 Debugging Experience

#### Enhanced Logging
```python
# Localhost-optimized logging
INFO: 🔄 File changed: ./agent.py
INFO: 🔍 Reloading agent...
INFO: ✅ Agent reloaded successfully
INFO: 🌐 Server ready: http://localhost:8080/
```

#### Error Recovery
- Graceful handling of agent loading errors
- Server stays running during temporary code issues
- Clear error messages with fix suggestions

## 6. Implementation Plan

### 6.1 Phase 1: Separate Pipeline Foundation (2-3 weeks)

#### Week 1: Pipeline Divergence
- [ ] Add `--localhost` CLI flag to cli.py
- [ ] Create `LocalhostOrchestrator` class (separate from `AgentOrchestrator`)
- [ ] Implement pipeline divergence at CLI entry point (line ~365)
- [ ] Reuse existing components: FrameworkDetector, EnvironmentLoader, PortChecker

#### Week 2: Localhost FastAPI Generation
- [ ] Create `LocalhostFastAPIGenerator` class
- [ ] Generate same A2A endpoints as Docker pipeline (health, agent-card, etc.)
- [ ] Implement `LocalhostServer` class with uvicorn integration
- [ ] Basic localhost serving without Docker

#### Week 3: Hot Reload & File Watching
- [ ] Implement `AgentFileWatcher` class
- [ ] Graceful server restart mechanisms  
- [ ] File change detection and filtering (.py, .env, requirements.txt)
- [ ] Error handling and recovery during reload

### 6.2 Phase 2: Developer Experience (1-2 weeks)

#### Week 4: UI Integration & Enhanced CLI
- [ ] React dev server integration and proxy setup
- [ ] HMR (Hot Module Replacement) support
- [ ] Development-optimized error messages
- [ ] Progress indicators and status updates

#### Week 5: Testing & Polish
- [ ] Comprehensive localhost testing suite
- [ ] Performance optimization (startup time)
- [ ] Documentation and examples
- [ ] Integration with existing examples

### 6.3 Phase 3: Advanced Features (1 week)

#### Week 6: Production Parity
- [ ] Helmsman localhost integration
- [ ] Environment variable hot-reload
- [ ] Production config testing mode
- [ ] Localhost deployment validation

## 7. Success Metrics

### 7.1 Performance Targets

| Metric | Current (Docker) | Target (Localhost) |
|--------|-----------------|-------------------|
| **Initial Startup** | 30-60 seconds | < 10 seconds |
| **Code Change Iteration** | 30-60 seconds | < 5 seconds |
| **Agent Reload** | Full rebuild | < 2 seconds |
| **UI Refresh** | Manual | Automatic (HMR) |

### 7.2 Developer Experience Goals

- **90% faster** development iteration cycle
- **Zero manual setup** for localhost development
- **100% feature parity** with Docker pipeline
- **Seamless transition** from localhost to Docker deployment

### 7.3 Adoption Metrics

- Usage of `--localhost` flag in CI/CD pipelines
- Developer survey scores for local development experience
- Reduction in Docker-related development issues
- Time-to-first-agent metrics for new developers
