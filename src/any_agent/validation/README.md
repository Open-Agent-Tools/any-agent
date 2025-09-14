# Any Agent Testing Module

This module provides comprehensive testing capabilities for A2A (Agent-to-Agent) protocol validation and agent testing.

## Quick Start

```bash
# Test an agent running on port 8080
python -m any_agent.testing.cli validate 8080

# Verbose output with detailed results  
python -m any_agent.testing.cli validate 8080 --verbose

# Save results as JSON
python -m any_agent.testing.cli validate 8080 --format json --output results.json
```

## Module Structure

```
src/any_agent/testing/
├── __init__.py                 # Module initialization
├── README.md                   # This file
├── cli.py                      # Command line interface
├── a2a_message_tester.py      # Core A2A protocol testing
├── client.py                   # A2A test client
├── engine.py                   # Test discovery and execution engine  
├── enhanced_client.py          # Enhanced A2A client with additional features
├── adk_client.py              # Google ADK-specific testing client
├── validator.py               # Protocol validation utilities
└── pytest_plugin.py          # pytest integration
```

## Core Components

### A2AMessageTester

The main testing class that validates A2A protocol compliance:

```python
from any_agent.testing.a2a_message_tester import A2AMessageTester

async def test_agent():
    tester = A2AMessageTester(timeout=30)
    results = await tester.test_agent_a2a_protocol(8080)
    print(f"Success: {results['success']}")
```

**Test Scenarios:**
1. **Agent Card Discovery** - Validates `/.well-known/agent.json`
2. **Client Connection** - Tests A2A client initialization  
3. **Basic Message Exchange** - Validates message processing

### CLI Interface

Comprehensive command-line interface for testing:

- `validate` - Run core A2A validation tests
- `test` - Advanced protocol compliance testing
- `discover` - Method and capability discovery
- `call` - Invoke specific A2A methods
- `init-config` - Generate configuration files

### Test Clients

Multiple client implementations for different testing scenarios:

- **A2ATestClient** - General-purpose testing client
- **EnhancedA2ATestClient** - Advanced features and validation
- **ADKTestClient** - Google ADK-specific testing

## Usage Examples

### Command Line

```bash
# Basic validation
python -m any_agent.testing.cli validate 8080

# With configuration file
python -m any_agent.testing.cli test http://localhost:8080 --config test-config.yaml

# Method discovery
python -m any_agent.testing.cli discover http://localhost:8080

# Call specific method
python -m any_agent.testing.cli call http://localhost:8080 get_weather --params '{"location": "NYC"}'
```

### Programmatic Usage

```python
import asyncio
from any_agent.testing.a2a_message_tester import A2AMessageTester

async def main():
    tester = A2AMessageTester(timeout=30)
    
    # Test agent on port 8080
    results = await tester.test_agent_a2a_protocol(8080)
    
    if results["success"]:
        print("✅ All A2A tests passed!")
        for test in results["tests"]:
            status = "✅" if test["success"] else "❌"
            print(f"  {status} {test['scenario']}: {test['duration_ms']:.1f}ms")
    else:
        print(f"❌ Tests failed: {results.get('error')}")

asyncio.run(main())
```

### pytest Integration

```python
import pytest
from any_agent.testing.a2a_message_tester import A2AMessageTester

@pytest.mark.asyncio
async def test_agent_a2a_compliance():
    tester = A2AMessageTester(timeout=30)
    results = await tester.test_agent_a2a_protocol(8080)
    assert results["success"], f"A2A validation failed: {results.get('error')}"
```

## Configuration

### Environment Variables

- `A2A_TEST_TIMEOUT` - Default timeout for tests (default: 30)
- `A2A_TEST_ENDPOINT` - Default agent endpoint
- `A2A_TEST_VERBOSE` - Enable verbose output (true/false)

### Configuration File

```yaml
# a2a-config.yaml
endpoint: "http://localhost:8080"
timeout: 30.0
auth_type: "bearer" 
auth_token: "your-token"
verify_ssl: true
headers:
  User-Agent: "A2A-Testing/1.0"
```

## Output Formats

### Text (Default)
Human-readable test results with status indicators and timing.

### JSON
Structured data format for programmatic processing:
```json
{
  "success": true,
  "summary": {
    "total": 3,
    "passed": 3, 
    "failed": 0,
    "duration_ms": 1250.5
  },
  "tests": [
    {
      "scenario": "agent_card_discovery",
      "success": true,
      "duration_ms": 15.2,
      "details": {...}
    }
  ]
}
```

### JUnit XML
Standard XML format for CI/CD integration:
```xml
<testsuite name="A2A Protocol Validation" tests="3" failures="0" time="1.250">
  <testcase name="agent_card_discovery" time="0.015"/>
  <testcase name="client_connection" time="0.004"/>
  <testcase name="basic_message_exchange" time="1.203"/>
</testsuite>
```

## Dependencies

### Required
- `a2a-sdk>=0.1.0` - A2A protocol implementation
- `httpx>=0.24.0` - HTTP client
- `click>=8.0.0` - CLI framework

### Optional
- `pytest>=7.0.0` - For test integration
- `pyyaml>=6.0` - For YAML configuration files

## Error Handling

The testing harness provides comprehensive error handling:

### Common Error Types
- **Connection Errors** - Agent not reachable
- **Protocol Errors** - A2A protocol violations
- **Timeout Errors** - Operations exceed time limits
- **Validation Errors** - Agent card or response format issues

### Error Codes
- `0` - All tests passed
- `1` - Test failures or execution errors
- `2` - Configuration errors
- `3` - Dependency errors (e.g., missing a2a-sdk)

## Performance

### Benchmarks
Typical performance on standard hardware:

| Test Scenario | Duration |
|---------------|----------|
| Agent Card Discovery | 10-50ms |
| Client Connection | 5-20ms |
| Basic Message Exchange | 500-2000ms |
| **Total Suite** | **1000-3000ms** |

### Optimization Tips
- Use appropriate timeout values
- Run tests close to agent (network latency)
- Monitor agent resource usage
- Consider parallel testing for multiple agents

## Troubleshooting

### Debug Mode
```bash
python -m any_agent.testing.cli validate 8080 --verbose
```

### Common Issues

**Agent Not Found**
```
❌ Validation failed: Connection refused
```
Solution: Verify agent is running on specified port.

**A2A SDK Missing** 
```
a2a-sdk not available - install with: pip install a2a-sdk>=0.1.0
```
Solution: Install required dependency.

**Timeout Errors**
```
Request timeout after 30s
```
Solution: Increase timeout or optimize agent performance.

## Development

### Running Tests
```bash
pytest src/any_agent/testing/
```

### Code Quality
```bash
ruff check src/any_agent/testing/
mypy src/any_agent/testing/
```

### Adding New Tests
1. Extend `A2AMessageTester` class
2. Add CLI command if needed
3. Include comprehensive tests
4. Update documentation

## See Also

- **[A2A Testing Harness Guide](../../docs/A2A_Testing_Harness_Guide.md)** - Comprehensive user guide
- **[Any Agent Framework](../)** - Main framework documentation
- **[A2A Protocol Specification](https://a2a-protocol.org/)** - Protocol details