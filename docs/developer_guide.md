# Developer Guide: Any Agent Framework

## Development Setup

### Prerequisites
- Python 3.8+
- Docker
- UV (package manager)

### Quick Setup
```bash
# Clone and setup
git clone <repository>
cd any-agent
uv sync

# Quality checks
ruff format src/ && ruff check src/ --fix && mypy src/

# Run tests
pytest
```

## Architecture Overview

### 3-Layer Design
1. **Detection & Adaptation** - Framework detection and adapter generation
2. **Protocol Layer** - A2A, OpenAI-compatible, and custom protocol support
3. **Containerization** - Docker generation with standardized endpoints

### Shared Module Architecture
```
url_utils (foundational)
    ↓
url_builder (consolidated URL construction)
    ↓
chat_endpoints_generator + unified_ui_routes (specialized generators)
    ↓
ui_routes_generator (compatibility wrapper) + entrypoint_templates (orchestrator)
```

## Code Standards

### Naming Conventions
- **Functions**: Use descriptive verb_noun pattern (`extract_metadata`, `validate_agent`)
- **Variables**: Use full words over abbreviations (`description_patterns` not `desc_patterns`)
- **Classes**: Prefer singular (`ValidationResult` not `ValidationResults`)
- **Private methods**: Clear purpose in name (`_combine_python_files`)
- **Exception handling**: Descriptive variable names (`connection_error` not `e`)

### Quality Requirements
- Type hints required (`disallow_untyped_defs = true`)
- 88 character line limit
- Always use UV for venv, pip, pytest, ruff, mypy
- Follow project requirements and dependencies

## Testing

### A2A Testing Harness
Comprehensive validation tool for A2A protocol compliance:

```bash
# Run A2A validation
python -m any_agent.testing.a2a_harness \
  --base-url http://localhost:3080 \
  --output-format json \
  --timeout 30
```

### Core Test Scenarios
1. **Agent Card Discovery** - Validates `/.well-known/agent-card.json`
2. **Client Connection** - Tests A2A client initialization
3. **Basic Message Exchange** - Sends test message to agent

### Framework Testing
- **Google ADK**: Use `examples/Google_ADK/Testing_Tessie/`
- **AWS Strands**: Use `examples/AWS_Strands/Product_Pete/`
- **Test Coverage**: 381 tests across all modules

## Framework Development

### Google ADK Setup
```bash
# Install dependencies
pip install google-genai google-adk

# Environment variables
export GOOGLE_API_KEY=your_key
export GOOGLE_MODEL=gemini-2.0-flash

# Test agent
python -m any_agent ./examples/Google_ADK/Testing_Tessie/
```

### Adding New Frameworks
1. Create detection patterns in `src/any_agent/core/detection/`
2. Implement adapter in `src/any_agent/adapters/`
3. Add test cases and validation
4. Update framework support matrix

## Module Boundaries

### Core Components
- **Framework Detection**: Pattern-based with confidence scoring
- **Configurable Adapters**: 95% code reduction through configuration
- **Context Management**: Thread-safe session isolation
- **Docker/Localhost Orchestrators**: Hot reload, health checks

### Shared Modules
- **URL Builder**: Consolidated URL construction
- **Context Manager**: Framework-specific context strategies
- **UI Routes**: Unified interface generation
- **Template Generator**: Docker and FastAPI templates

## Contributing

1. Follow code standards and naming conventions
2. Add comprehensive tests for new features
3. Update documentation for user-facing changes
4. Ensure all quality checks pass
5. Test across multiple frameworks

## Tools
- **Package Management**: UV
- **Code Quality**: ruff, black, mypy
- **Testing**: pytest
- **UI Development**: React + TypeScript + Material-UI + Vite