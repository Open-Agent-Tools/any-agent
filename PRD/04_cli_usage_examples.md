# CLI Usage Examples: Any Agent Framework v0.1.7

## 1. Quick Start Examples

### 1.1 Basic Agent Containerization
```bash
# Auto-detect framework and containerize
python -m any_agent ./my_agent/

# With specific port
python -m any_agent ./my_agent/ --port 3080

# With UI enabled (default)
python -m any_agent ./my_agent/ --port 3080
```

### 1.2 Framework-Specific Examples

#### Google ADK Agents
```bash
# Auto-detection (recommended)
python -m any_agent ./examples/Google_ADK/Testing_Tessie/

# Manual framework specification
python -m any_agent ./adk_agent/ --framework google_adk --port 8035

# With environment variables
GOOGLE_API_KEY=your_key python -m any_agent ./adk_agent/
```

#### AWS Strands Agents
```bash
# Auto-detection with A2A context isolation
python -m any_agent ./strands_agent/ --port 8040

# With environment configuration
ANTHROPIC_API_KEY=your_key python -m any_agent ./strands_agent/

# With MCP server integration
MCP_SERVER_URL=http://localhost:3001 python -m any_agent ./strands_agent/
```

#### LangChain Agents
```bash
# Generic framework approach with instance copying
python -m any_agent ./langchain_agent/ --framework langchain

# With custom port and UI
python -m any_agent ./langchain_agent/ --port 9000
```

## 2. Development Workflow

### 2.1 Localhost Development Mode
```bash
# Start development server with hot reload
python -m any_agent ./my_agent/ --localhost --port 8080

# Development mode with file watching
python -m any_agent ./my_agent/ --localhost --watch

# Development without UI (API only)
python -m any_agent ./my_agent/ --localhost --no-ui
```

#### Development Output Example
```
🚀 Starting localhost server on port 8080...
📁 Watching for file changes in ./my_agent/
🔍 Framework detected: google_adk (confidence: 0.95)
✅ Agent loaded: Testing_Tessie Agent
🌐 Server ready!
   🌐 Agent URL: http://localhost:8080/
   🏥 Health Check: http://localhost:8080/health
   📋 Agent Card: http://localhost:8080/.well-known/agent-card.json
   💬 Chat UI: http://localhost:8080/
```

### 2.2 Production Build
```bash
# Build Docker container for production
python -m any_agent ./my_agent/ --port 3080

# Build with custom image name
python -m any_agent ./my_agent/ --image-name my-agent:v1.0

# Build and push to registry
python -m any_agent ./my_agent/ --push --registry myregistry.com
```

### 2.3 Validation and Testing
```bash
# Dry run to validate without building
python -m any_agent ./my_agent/ --dry-run

# Validate with detailed output
python -m any_agent ./my_agent/ --validate --verbose

# Framework detection only
python -m any_agent ./my_agent/ --detect-only
```

## 3. Advanced Usage Patterns

### 3.1 Helmsman Registry Integration
```bash
# Register with default Helmsman instance
python -m any_agent ./my_agent/ --helmsman

# Register with custom Helmsman URL
HELMSMAN_URL=http://my-registry:7080 python -m any_agent ./my_agent/ --helmsman

# Register with authentication
HELMSMAN_TOKEN=your_token python -m any_agent ./my_agent/ --helmsman --agent-id my-unique-agent
```

#### Registry Registration Output
```
🔍 Framework detected: aws_strands (confidence: 0.92)
🏗️  Building container image...
✅ Container built successfully: agent-container:latest
📋 Generated agent card with capabilities
🌐 Registering with Helmsman at http://localhost:7080
✅ Agent registered successfully
   📍 Registry URL: http://localhost:7080/agents/my-agent
   🔗 Agent URL: http://localhost:3080
```

### 3.2 Environment Configuration
```bash
# Framework-specific environment variables
GOOGLE_API_KEY=your_key \
GOOGLE_MODEL=gemini-1.5-flash \
python -m any_agent ./adk_agent/

# AWS Strands with multiple variables
ANTHROPIC_API_KEY=your_key \
AWS_REGION=us-west-2 \
MCP_SERVER_URL=http://localhost:3001 \
python -m any_agent ./strands_agent/

# Generic framework configuration
AGENT_PORT=8080 \
OPENAI_API_KEY=your_key \
python -m any_agent ./generic_agent/
```

### 3.3 UI and Interface Configuration
```bash
# Disable web UI (API only)
python -m any_agent ./my_agent/ --no-ui

# Force UI rebuild
python -m any_agent ./my_agent/ --rebuild-ui

# Custom static file serving
python -m any_agent ./my_agent/ --static-dir ./custom_ui/
```

## 4. Framework-Specific Workflows

### 4.1 Google ADK Complete Workflow
```bash
# 1. Development
python -m any_agent ./examples/Google_ADK/Testing_Tessie/ --localhost

# 2. Validation
python -m any_agent ./examples/Google_ADK/Testing_Tessie/ --dry-run --validate

# 3. Production build
GOOGLE_API_KEY=your_key python -m any_agent ./examples/Google_ADK/Testing_Tessie/ --port 8035

# 4. Registry registration
python -m any_agent ./examples/Google_ADK/Testing_Tessie/ --helmsman --port 8035
```

### 4.2 AWS Strands with Context Isolation
```bash
# Development with session management
python -m any_agent ./strands_agent/ --localhost --port 8040

# Production with A2A context isolation
ANTHROPIC_API_KEY=your_key python -m any_agent ./strands_agent/ --port 8040

# Multi-session testing
curl -X POST http://localhost:8040/chat/create-session \
  -H "Content-Type: application/json" \
  -d '{"session_id": "user1"}'

curl -X POST http://localhost:8040/chat/create-session \
  -H "Content-Type: application/json" \
  -d '{"session_id": "user2"}'
```

### 4.3 LangChain Agent with Generic Wrapper
```bash
# Force generic framework detection
python -m any_agent ./langchain_agent/ --framework generic

# With custom context isolation
python -m any_agent ./langchain_agent/ --context-isolation instance-copy

# Performance monitoring
python -m any_agent ./langchain_agent/ --monitor --metrics-port 9090
```

## 5. Troubleshooting and Debugging

### 5.1 Framework Detection Issues
```bash
# Manual framework specification
python -m any_agent ./my_agent/ --framework google_adk

# Verbose detection output
python -m any_agent ./my_agent/ --detect-only --verbose

# Framework detection confidence
python -m any_agent ./my_agent/ --show-confidence
```

### 5.2 Validation and Error Handling
```bash
# Comprehensive validation
python -m any_agent ./my_agent/ --validate --verbose

# Check agent requirements
python -m any_agent ./my_agent/ --check-requirements

# Validate agent card generation
python -m any_agent ./my_agent/ --validate-agent-card
```

#### Common Validation Errors
```
❌ Validation failed: Missing required __init__.py file
   💡 Suggestion: Ensure your agent package has __init__.py with root_agent export

❌ Framework detection confidence too low (0.3)
   💡 Suggestion: Use --framework flag to specify framework manually

❌ Agent loading failed: ModuleNotFoundError
   💡 Suggestion: Check relative imports and ensure all dependencies are available
```

### 5.3 Container and Deployment Issues
```bash
# Build with detailed logs
python -m any_agent ./my_agent/ --verbose --build-logs

# Health check validation
python -m any_agent ./my_agent/ --health-check --timeout 60

# Container startup debugging
python -m any_agent ./my_agent/ --debug --container-logs
```

## 6. Batch Operations and Automation

### 6.1 Multiple Agent Processing
```bash
# Process multiple agents
for agent in ./agents/*/; do
  echo "Processing $agent..."
  python -m any_agent "$agent" --port $((8000 + $(echo $agent | tr -dc '0-9')))
done

# Batch validation
find ./agents -name "*.py" -path "*/agent.py" | while read agent; do
  python -m any_agent "$(dirname "$agent")" --dry-run --validate
done
```

### 6.2 CI/CD Integration
```bash
# GitHub Actions example
name: Build and Deploy Agent
steps:
  - name: Validate Agent
    run: python -m any_agent ./my_agent/ --dry-run --validate

  - name: Build Container
    run: python -m any_agent ./my_agent/ --port 3080

  - name: Register with Helmsman
    run: python -m any_agent ./my_agent/ --helmsman --port 3080
    env:
      HELMSMAN_URL: ${{ secrets.HELMSMAN_URL }}
      HELMSMAN_TOKEN: ${{ secrets.HELMSMAN_TOKEN }}
```

### 6.3 Configuration Management
```bash
# Using configuration file
cat > agent_config.yaml << EOF
agent:
  name: "My Production Agent"
  framework: "auto"
container:
  port: 3080
  enable_ui: true
protocols:
  a2a_enabled: true
helmsman:
  register: true
EOF

python -m any_agent ./my_agent/ --config agent_config.yaml
```

## 7. Performance and Monitoring

### 7.1 Performance Testing
```bash
# Load testing endpoints
ab -n 1000 -c 10 http://localhost:8080/health
ab -n 100 -c 5 -T 'application/json' -p message.json http://localhost:8080/message:send

# Context isolation performance
for i in {1..10}; do
  curl -X POST http://localhost:8080/chat/create-session \
    -H "Content-Type: application/json" \
    -d "{\"session_id\": \"perf_test_$i\"}" &
done
```

### 7.2 Monitoring Integration
```bash
# With Prometheus metrics
python -m any_agent ./my_agent/ --metrics --metrics-port 9090

# Health check monitoring
watch -n 5 'curl -s http://localhost:8080/health | jq'

# Container resource monitoring
docker stats agent-container
```

## 8. Advanced Configuration Examples

### 8.1 Custom Entrypoint Generation
```bash
# Generate custom entrypoint without building
python -m any_agent ./my_agent/ --generate-entrypoint --output ./custom_entrypoint.py

# Use custom template
python -m any_agent ./my_agent/ --template-dir ./custom_templates/
```

### 8.2 Development vs Production Modes
```bash
# Development configuration
python -m any_agent ./my_agent/ \
  --localhost \
  --hot-reload \
  --debug \
  --ui-dev-server \
  --port 8080

# Production configuration
python -m any_agent ./my_agent/ \
  --port 3080 \
  --health-check \
  --optimize \
  --security-hardening
```

### 8.3 Framework Migration
```bash
# Migrate from manual container to Any Agent
# 1. Analyze existing setup
python -m any_agent ./existing_agent/ --analyze --compare-dockerfile

# 2. Generate compatible configuration
python -m any_agent ./existing_agent/ --generate-config --output config.yaml

# 3. Validate migration
python -m any_agent ./existing_agent/ --config config.yaml --dry-run

# 4. Execute migration
python -m any_agent ./existing_agent/ --config config.yaml
```

This comprehensive CLI guide covers all major usage patterns for Any Agent Framework v0.1.7, including the new consolidated architecture features, context isolation capabilities, and framework-specific optimizations.