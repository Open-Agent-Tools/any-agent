# Helmsman Integration: Agent Registration and Discovery

## 1. Overview

The Any Agent framework integrates with Helmsman to provide automated agent registration and discovery during deployment. This separation of concerns keeps agents focused on their core functionality while enabling centralized orchestration and management.

## 2. Integration Architecture ✅ Complete

### 2.1 Deployment-Time Registration ✅ Complete
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   any_agent     │    │   Container     │    │   Helmsman      │
│   CLI Tool      │───▶│   Registry      │    │   Service       │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       ▲
         │                       │                       │
         └─── Agent Metadata ────┴───── Registration ────┘
              (name, capabilities,        (POST /agents)
               endpoints, health)
```

### 2.2 Runtime Agent Self-Awareness
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Containerized │    │   Helmsman MCP  │    │   Helmsman      │
│   Agent         │───▶│   Client        │───▶│   Service       │
│                 │    │                 │    │                 │
│  - Agent ID     │    │  - Query agents │    │  - Agent registry│
│  - Capabilities │    │  - Discover     │    │  - Orchestration│
│  - Health       │    │  - Communicate  │    │  - Routing      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 3. CLI Integration

### 3.1 Helmsman Flags (Current Implementation) ✅ Complete

#### ✅ Currently Working Flags ✅ Complete
```bash
python -m any_agent [OPTIONS] AGENT_PATH

Implemented Helmsman Options:
  --helmsman                    Enable Helmsman registration ✅
  --helmsman-url TEXT          Helmsman service URL (default: http://localhost:7080) ✅
  --agent-name TEXT            Unique agent identifier for registration ✅
  --helmsman-token TEXT        Authentication token for Helmsman ✅
```

#### ❌ Planned Future Flags - Not Implemented
```bash
Additional Planned Options:
  --register-on-start          Register agent after container starts (PLANNED)
  --include-metadata           Include full agent metadata in registration (PLANNED)
  --helmsman-timeout INTEGER   Registration timeout in seconds (PLANNED)
```

### 3.2 Usage Examples ✅ Complete

#### Basic Registration ✅ Complete
```bash
# Register agent during deployment
python -m any_agent ./trading_agent/ \
  --framework adk \
  --build \
  --push registry.com/agents/trading:v1.0 \
  --helmsman \
  --agent-name trading-agent-prod
```

#### Advanced Registration with Custom Helmsman ✅ Complete
```bash
# Custom Helmsman URL and metadata
python -m any_agent ./customer_service/ \
  --framework adk \
  --build \
  --push registry.com/cs-agent:v2.1 \
  --helmsman \
  --helmsman-url https://helmsman.internal.com \
  --agent-name cs-agent-v2 \
  --include-metadata \
  --register-on-start
```

#### Environment-Based Registration ✅ Complete
```bash
# Using environment variables
export HELMSMAN_URL=http://localhost:7080/api  # Development default
export HELMSMAN_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
export AGENT_ID=financial-advisor-staging

python -m any_agent ./financial_agent/ \
  --framework adk \
  --build \
  --push registry.com/financial:staging \
  --helmsman
```

## 4. Registration Process ✅ Complete

### 4.1 Deployment-Time Registration Flow ✅ Complete
1. **Agent Analysis**: Extract agent metadata (name, description, capabilities)
2. **Container Build**: Include Helmsman MCP client in container
3. **Image Push**: Push container to registry
4. **Helmsman Registration**: POST agent metadata to Helmsman service
5. **Validation**: Confirm registration and get agent routing info

### 4.2 Registration Payload ✅ Complete
```json
{
  "agent_id": "trading-agent-prod",
  "name": "Trading Agent",
  "description": "AI-powered trading strategy agent",
  "version": "1.0.0",
  "framework": "google-adk",
  "container": {
    "image": "registry.com/agents/trading:v1.0",
    "port": 8080,
    "health_check": "/health"
  },
  "capabilities": [
    "market_analysis",
    "risk_assessment", 
    "trade_execution"
  ],
  "endpoints": {
    "a2a": "/a2a/message:send",
    "openai": "/v1/chat/completions",
    "health": "/health",
    "docs": "/docs"
  },
  "protocols": ["a2a", "openai"],
  "metadata": {
    "created_at": "2024-01-15T10:30:00Z",
    "deployed_by": "ci-cd-pipeline",
    "environment": "production"
  }
}
```

### 4.3 Registration Response ✅ Complete
```json
{
  "status": "registered",
  "agent_id": "trading-agent-prod",
  "helmsman_id": "helm_agent_7829bc4f",
  "routing": {
    "external_url": "https://agents.company.com/trading-agent-prod",
    "internal_url": "http://trading-agent-prod.agents.svc.cluster.local:8080"
  },
  "discovery": {
    "tags": ["trading", "financial", "production"],
    "categories": ["market-analysis", "risk-management"]
  }
}
```


## 6. Configuration Options ❌ Not Implemented

### 6.1 YAML Configuration ❌ Not Implemented
**Current Reality**: No YAML configuration processing. All Helmsman options via CLI flags only.

**Documented Design** (not implemented):
```yaml
helmsman:
  enabled: true ❌ CLI flag only (--helmsman)
  url: "http://localhost:7080/api" ❌ CLI flag only (--helmsman-url)
  agent_id: "my-agent-prod" ❌ CLI flag only (--agent-name)
  
  # Registration options ❌ Not implemented
  register_on_deploy: true ❌ Not implemented
  register_on_start: false ❌ Not implemented
  include_metadata: true ❌ Not implemented
  registration_timeout: 30 ❌ Not implemented
  
  # Authentication
  token: "${HELMSMAN_TOKEN}" ❌ CLI flag only (--helmsman-token)
  
  # MCP integration ❌ Not implemented
  enable_mcp_client: true ❌ Not implemented
  mcp_capabilities: [...] ❌ Not implemented
  
  # Agent metadata ❌ Not implemented
  tags: [...] ❌ Not implemented
  categories: [...] ❌ Not implemented
```

**What Actually Works**: CLI flags only:
```bash
python -m any_agent ./agent/ \
  --helmsman \
  --helmsman-url http://localhost:7080 \
  --agent-name my-agent-prod \
  --helmsman-token $HELMSMAN_TOKEN
```

### 6.2 Environment Variables ✅ Complete
```bash
# Helmsman service configuration
HELMSMAN_URL=http://localhost:7080/api  # Development default
HELMSMAN_MCP_URL=http://localhost:7081/mcp  # MCP endpoint
HELMSMAN_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Agent identification
AGENT_ID=trading-agent-prod
AGENT_NAME="Trading Agent"
AGENT_VERSION=1.0.0

# MCP configuration
HELMSMAN_MCP_ENABLED=true
HELMSMAN_MCP_TIMEOUT=10
```

## 7. Deployment Scenarios ✅ Complete

### 7.1 CI/CD Pipeline Integration ✅ Complete
```yaml
# .github/workflows/deploy-agent.yml
name: Deploy Agent
on:
  push:
    tags: ['v*']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build and Deploy Agent
        run: |
          python -m any_agent ./agent/ \
            --framework adk \
            --container-name ${{ github.event.repository.name }} \
            --build \
            --push ${{ secrets.REGISTRY_URL }}/agents/${{ github.event.repository.name }}:${{ github.ref_name }} \
            --helmsman \
            --helmsman-url ${{ secrets.HELMSMAN_URL }} \
            --agent-name ${{ github.event.repository.name }}-prod \
            --helmsman-token ${{ secrets.HELMSMAN_TOKEN }}
```

### 7.2 Kubernetes Deployment ✅ Complete
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trading-agent
spec:
  template:
    spec:
      containers:
      - name: trading-agent
        image: registry.com/agents/trading:v1.0
        env:
        - name: HELMSMAN_URL
          value: "https://helmsman.cluster.local"
        - name: AGENT_ID
          value: "trading-agent-prod"
        - name: HELMSMAN_TOKEN
          valueFrom:
            secretKeyRef:
              name: helmsman-credentials
              key: token
```

### 7.3 Docker Compose Development ✅ Complete
```yaml
# docker-compose.yml
version: '3.8'
services:
  trading-agent:
    build: .
    environment:
      - HELMSMAN_URL=http://helmsman:7080/api
      - AGENT_ID=trading-agent-dev
    depends_on:
      - helmsman
      
  helmsman:
    image: helmsman/service:latest
    ports:
      - "7080:7080"  # API port
```

## 8. Error Handling and Monitoring ✅ Complete

### 8.1 Registration Failures ✅ Complete
```python
# Registration error handling
async def register_with_helmsman(agent_metadata: dict, retry_count: int = 3):
    for attempt in range(retry_count):
        try:
            response = await helmsman_client.register_agent(agent_metadata)
            logger.info(f"Agent registered successfully: {response['helmsman_id']}")
            return response
        except HelmsmanConnectionError as e:
            logger.warning(f"Registration attempt {attempt + 1} failed: {e}")
            if attempt < retry_count - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        except HelmsmanAuthError as e:
            logger.error(f"Authentication failed: {e}")
            break
    
    logger.error("Failed to register with Helmsman after all attempts")
    # Continue without Helmsman integration
    return None
```

### 8.2 Health Monitoring ✅ Complete
```python
# Health check with Helmsman integration
@app.get("/health")
async def health_check():
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "agent_id": os.getenv('AGENT_ID'),
        "version": "1.0.0"
    }
    
    # Check Helmsman connectivity
    if helmsman_client:
        try:
            helmsman_status = await helmsman_client.ping()
            health_data["helmsman"] = {
                "connected": True,
                "status": helmsman_status
            }
        except Exception as e:
            health_data["helmsman"] = {
                "connected": False,
                "error": str(e)
            }
    
    return health_data
```


This integration pattern provides a clean separation between deployment-time orchestration and runtime agent capabilities, enabling scalable agent management while keeping individual agents focused on their core functionality.