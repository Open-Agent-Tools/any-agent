# A2A Testing Harness - User Guide

## Overview

The A2A Testing Harness is a comprehensive validation tool for Agent-to-Agent (A2A) protocol compliance. It provides automated testing capabilities to ensure deployed agents correctly implement the A2A communication protocol.

## Features

- **Automated Protocol Validation**: Tests the 3 core A2A scenarios
- **Multiple Output Formats**: Text, JSON, and JUnit XML reporting  
- **Flexible CLI Interface**: Easy integration with CI/CD pipelines
- **Framework Agnostic**: Works with any A2A-compliant agent
- **Comprehensive Reporting**: Detailed test results and performance metrics

## Core Test Scenarios

The harness validates three essential A2A protocol functions:

### 1. Agent Card Discovery
- Validates agent card retrieval from `/.well-known/agent.json`
- Checks required fields: name, version, capabilities
- Verifies JSON structure and data types

### 2. Client Connection
- Tests A2A client factory initialization
- Validates connection establishment
- Confirms client configuration

### 3. Basic Message Exchange
- Sends test message to agent
- Validates JSON-RPC 2.0 response format
- Checks message processing capabilities

## Installation

The A2A Testing Harness is included with the Any Agent Framework:

```bash
pip install -e ".[dev]"  # Install with development dependencies
```

Required dependencies:
- `a2a-sdk>=0.1.0` - A2A protocol implementation
- `click>=8.0` - CLI framework
- `httpx>=0.24` - HTTP client

## Quick Start

### Basic Usage

Test an agent running on the default port (8080):
```bash
python -m any_agent.testing.cli validate
```

Test an agent on a specific port:
```bash
python -m any_agent.testing.cli validate 8035
```

### Verbose Output

Get detailed test information:
```bash
python -m any_agent.testing.cli validate 8035 --verbose
```

Example output:
```
🚀 A2A Protocol Validation
📡 Testing agent on port 8035
⏱️  Timeout: 30s

🧪 A2A Protocol Validation Report
========================================
✅ Overall Status: PASSED
📊 Tests: 3 total, 3 passed, 0 failed
⏱️  Duration: 1414.4ms

📋 Test Details:
  ✅ agent_card_discovery: 15.8ms
  ✅ client_connection: 4.3ms  
  ✅ basic_message_exchange: 1203.3ms
```

### Save Results to File

Save test results for later analysis:
```bash
# Save as JSON
python -m any_agent.testing.cli validate 8035 --format json --output results.json

# Save as JUnit XML (for CI integration)  
python -m any_agent.testing.cli validate 8035 --format junit --output test-results.xml
```

## CLI Commands

The A2A Testing Harness provides several CLI commands:

### `validate` - Core Validation Tests

Run the comprehensive 3-test validation suite:

```bash
python -m any_agent.testing.cli validate [PORT] [OPTIONS]
```

**Arguments:**
- `PORT` - Agent port number (default: 8080)

**Options:**
- `--timeout INTEGER` - Timeout in seconds (default: 30)
- `-v, --verbose` - Enable detailed output
- `--format [text|json|junit]` - Output format (default: text)
- `-o, --output PATH` - Save results to file

### `test` - Advanced Testing

Run comprehensive protocol compliance tests:

```bash
python -m any_agent.testing.cli test [ENDPOINT] [OPTIONS]
```

**Arguments:**
- `ENDPOINT` - Full agent URL (default: http://localhost:8080)

**Options:**
- `-c, --config PATH` - Configuration file
- `--auth-token TEXT` - Authentication token
- `--auth-type [bearer|api_key]` - Auth type (default: bearer)
- `--timeout FLOAT` - Request timeout (default: 30.0)
- `--format [text|json|junit]` - Output format
- `-o, --output PATH` - Output file
- `-v, --verbose` - Verbose output

### `discover` - Method Discovery

Discover available A2A methods and capabilities:

```bash
python -m any_agent.testing.cli discover [ENDPOINT] [OPTIONS]
```

### `call` - Method Invocation

Call specific A2A methods for testing:

```bash
python -m any_agent.testing.cli call [ENDPOINT] [METHOD] [OPTIONS]
```

**Options:**
- `--params TEXT` - JSON parameters for method call
- `--validate/--no-validate` - Enable/disable JSON-RPC validation (default: enabled)

### `init-config` - Configuration Generation

Generate sample configuration files:

```bash
python -m any_agent.testing.cli init-config
```

## Configuration

### Configuration File Format

Create a YAML configuration file for complex testing scenarios:

```yaml
# a2a-test-config.yaml
endpoint: "http://localhost:8080"
timeout: 30.0
auth_type: "bearer"
auth_token: "your-token-here"
verify_ssl: true
headers:
  User-Agent: "A2A-Testing-Harness/1.0"
  X-Test-Environment: "development"

# Test execution options
test_options:
  retry_count: 3
  retry_delay: 1.0
  fail_fast: false
```

Use the configuration:
```bash
python -m any_agent.testing.cli test --config a2a-test-config.yaml
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: A2A Protocol Tests
on: [push, pull_request]

jobs:
  a2a-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      
      - name: Start test agent
        run: |
          python -m any_agent examples/adk_agent_only --port 8080 &
          sleep 10  # Wait for agent startup
      
      - name: Run A2A validation tests  
        run: |
          python -m any_agent.testing.cli validate 8080 \
            --format junit --output a2a-results.xml
      
      - name: Publish test results
        uses: dorny/test-reporter@v1
        if: success() || failure()
        with:
          name: A2A Protocol Tests
          path: a2a-results.xml
          reporter: java-junit
```

### Jenkins Pipeline Example

```groovy
pipeline {
    agent any
    stages {
        stage('Setup') {
            steps {
                sh 'pip install -e ".[dev]"'
            }
        }
        stage('Deploy Test Agent') {
            steps {
                sh '''
                    python -m any_agent examples/adk_agent_only --port 8080 &
                    echo $! > agent.pid
                    sleep 10
                '''
            }
        }
        stage('A2A Validation') {
            steps {
                sh '''
                    python -m any_agent.testing.cli validate 8080 \
                      --format junit --output test-results.xml
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                    sh 'kill $(cat agent.pid) || true'
                }
            }
        }
    }
}
```

## Programmatic Usage

### Using A2AMessageTester Directly

For custom testing scenarios, use the `A2AMessageTester` class directly:

```python
import asyncio
from any_agent.testing.a2a_message_tester import A2AMessageTester

async def test_my_agent():
    tester = A2AMessageTester(timeout=30)
    
    # Test agent on port 8080
    results = await tester.test_agent_a2a_protocol(8080)
    
    if results["success"]:
        print("✅ All tests passed!")
        print(f"Duration: {results['summary']['duration_ms']:.1f}ms")
    else:
        print("❌ Tests failed!")
        print(f"Error: {results.get('error', 'Unknown error')}")
    
    return results

# Run the test
results = asyncio.run(test_my_agent())
```

### Custom Test Integration

Integrate A2A validation into your existing test suites:

```python
import pytest
from any_agent.testing.a2a_message_tester import A2AMessageTester

@pytest.mark.asyncio
async def test_agent_a2a_compliance(agent_port):
    """Test that deployed agent meets A2A protocol requirements."""
    tester = A2AMessageTester(timeout=30)
    results = await tester.test_agent_a2a_protocol(agent_port)
    
    # Assert overall success
    assert results["success"], f"A2A tests failed: {results.get('error')}"
    
    # Check individual test scenarios
    tests = results["tests"]
    assert len(tests) == 3, "Expected 3 core A2A tests"
    
    # Validate specific scenarios
    test_scenarios = {test["scenario"]: test for test in tests}
    
    assert test_scenarios["agent_card_discovery"]["success"], "Agent card discovery failed"
    assert test_scenarios["client_connection"]["success"], "Client connection failed"  
    assert test_scenarios["basic_message_exchange"]["success"], "Message exchange failed"
    
    # Performance check
    total_duration = results["summary"]["duration_ms"]
    assert total_duration < 5000, f"Tests took too long: {total_duration}ms"
```

## Troubleshooting

### Common Issues

**1. Agent Not Responding**
```
❌ Validation failed: Failed to connect to A2A server: ...
```
**Solution**: Verify agent is running and accessible on the specified port.

**2. A2A SDK Not Available**
```
a2a-sdk not available - install with: pip install a2a-sdk>=0.1.0
```
**Solution**: Install the A2A SDK dependency.

**3. Agent Card Not Found**
```
Agent card discovery failed: 404 Not Found
```
**Solution**: Ensure agent exposes agent card at `/.well-known/agent.json`.

**4. Timeout Errors**
```
Request timeout after 30s
```
**Solution**: Increase timeout with `--timeout 60` or optimize agent response time.

### Debug Mode

Enable verbose logging for detailed troubleshooting:

```bash
python -m any_agent.testing.cli validate 8080 --verbose
```

### Checking Agent Health

Before running A2A tests, verify agent health:

```bash
curl http://localhost:8080/health
```

Expected response:
```json
{"status": "healthy", "service": "a2a-agent"}
```

## Extension and Customization

### Creating Custom Test Scenarios

Extend the `A2AMessageTester` class for custom validation:

```python
from any_agent.testing.a2a_message_tester import A2AMessageTester, A2ATestResult
import time

class CustomA2AMessageTester(A2AMessageTester):
    """Extended tester with custom scenarios."""
    
    async def test_custom_scenario(self, port: int) -> dict:
        """Add custom test scenario."""
        # Run standard tests
        results = await self.test_agent_a2a_protocol(port)
        
        # Add custom test
        await self._test_performance_benchmark(f"http://localhost:{port}")
        
        return results
    
    async def _test_performance_benchmark(self, base_url: str) -> None:
        """Custom performance testing scenario."""
        scenario = "performance_benchmark"
        start_time = time.time()
        
        try:
            # Implement custom test logic
            # ... your testing code here ...
            
            duration_ms = (time.time() - start_time) * 1000
            
            self.test_results.append(
                A2ATestResult(
                    scenario=scenario,
                    success=True,
                    duration_ms=duration_ms,
                    details={"benchmark": "passed"}
                )
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.test_results.append(
                A2ATestResult(
                    scenario=scenario,
                    success=False,
                    duration_ms=duration_ms, 
                    details={},
                    error=str(e)
                )
            )
```

### Custom CLI Commands

Add new commands to the testing CLI:

```python
import click
from any_agent.testing.cli import cli

@cli.command()
@click.argument("port", type=int)
@click.option("--iterations", type=int, default=10)
def benchmark(port: int, iterations: int) -> None:
    """Run performance benchmark tests."""
    click.echo(f"Running {iterations} benchmark iterations on port {port}")
    # Implement benchmark logic
```

### Integration with Testing Frameworks

#### pytest Plugin

Create a pytest plugin for A2A testing:

```python
# conftest.py
import pytest
from any_agent.testing.a2a_message_tester import A2AMessageTester

@pytest.fixture
async def a2a_tester():
    """Provide A2A tester instance."""
    return A2AMessageTester(timeout=30)

@pytest.fixture 
def a2a_agent_port():
    """Provide agent port for testing."""
    return 8080  # Configure as needed
```

#### unittest Integration

```python
import unittest
from any_agent.testing.a2a_message_tester import A2AMessageTester

class TestA2ACompliance(unittest.TestCase):
    
    def setUp(self):
        self.tester = A2AMessageTester(timeout=30)
        self.agent_port = 8080
    
    async def test_a2a_protocol(self):
        results = await self.tester.test_agent_a2a_protocol(self.agent_port)
        self.assertTrue(results["success"])
        self.assertEqual(len(results["tests"]), 3)
```

## Performance Considerations

### Optimization Tips

1. **Timeout Settings**: Use appropriate timeouts based on agent complexity
2. **Parallel Testing**: Run multiple agent tests concurrently when possible  
3. **Resource Monitoring**: Monitor agent resource usage during testing
4. **Test Scheduling**: Schedule intensive tests during off-peak hours

### Performance Benchmarks

Expected performance ranges for typical agents:

| Test Scenario | Target Duration | Maximum Acceptable |
|---------------|-----------------|-------------------|
| Agent Card Discovery | < 50ms | < 500ms |
| Client Connection | < 100ms | < 1000ms | 
| Basic Message Exchange | < 2000ms | < 10000ms |
| **Total Test Suite** | **< 3000ms** | **< 15000ms** |

## Support and Contributing

### Getting Help

- **Documentation**: This guide and inline CLI help (`--help`)
- **Issues**: Report bugs and feature requests via project issues
- **Discussion**: Join project discussions for usage questions

### Contributing

To contribute to the A2A Testing Harness:

1. Follow the project's coding standards (ruff, mypy, pytest)
2. Add comprehensive tests for new features
3. Update documentation for any changes
4. Submit pull requests with clear descriptions

### Development Setup

```bash
# Clone and setup development environment
git clone <repository-url>
cd any-agent
pip install -e ".[dev]"

# Run tests
pytest src/any_agent/testing/

# Check code quality  
ruff check src/any_agent/testing/
mypy src/any_agent/testing/
```

---

**Version**: 1.0  
**Last Updated**: 2025-08-29  
**Compatibility**: Any Agent Framework v1.0+, A2A SDK v0.1.0+