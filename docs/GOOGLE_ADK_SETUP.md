# Google ADK Test Agent Setup Guide

This guide explains how to set up and use the Google ADK test agent for developing and testing the Any Agent framework.

## Overview

The `adk_test_agent/` directory contains a working Google ADK agent that serves as:
- A reference implementation for Google ADK integration
- Test data for framework detection development
- Integration testing target
- Example of proper ADK agent structure

## Prerequisites

### 1. Google API Key

You need a Google API key to run Google ADK agents:

1. Go to the [Google AI Studio](https://aistudio.google.com/)
2. Create a new API key
3. Copy the API key to your environment

### 2. Google ADK Dependencies

The test agent requires Google ADK and related packages:

```bash
# Install Google ADK (if not already installed)
pip install google-genai google-adk

# Optional: Basic open agent tools for datetime functionality
pip install basic-open-agent-tools
```

## Configuration

### 1. Environment Variables

Copy the `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```bash
# Required for Google ADK
GOOGLE_API_KEY=your_actual_google_api_key_here
GOOGLE_MODEL=gemini-1.5-flash

# MCP server (for test agent functionality)
MCP_SERVER_URL=http://localhost:7081/mcp

# Optional: Vertex AI configuration
GOOGLE_GENAI_USE_VERTEXAI=FALSE
```

### 2. Test Agent Configuration

The test agent is configured via environment variables only. Key settings:

- **MCP_SERVER_URL**: URL for MCP server communication (default: `http://localhost:7081/mcp`)
- **GOOGLE_API_KEY**: Your Google API key for Gemini access
- **GOOGLE_MODEL**: Gemini model to use (default: `gemini-1.5-flash`)

## Agent Structure

The Google ADK test agent follows the standard ADK structure:

```
adk_test_agent/
├── __init__.py           # Package initialization
├── agent.py             # Main agent configuration
├── prompts.py           # Agent instructions and prompts
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (not in repo)
└── evals/              # Evaluation test cases
    ├── 00_mvp_list_available_tools_test.json
    └── test_config.json
```

### Key Components

#### `agent.py`
- **Purpose**: Main agent configuration and setup
- **Key Function**: `create_agent()` - Returns configured ADK Agent instance
- **Tools**: MCP toolset for external service communication
- **Global**: `root_agent` - The configured agent instance

#### `prompts.py`
- **Purpose**: Contains agent instructions and system prompts
- **Key Variable**: `agent_instruction` - Main instruction text for the agent

#### MCP Integration
- Uses `MCPToolset` with HTTP connection to MCP server
- Includes datetime tools for natural language time handling
- Configured for generic MCP server testing

## Running the Test Agent

### 1. Direct Agent Testing

Test the agent configuration directly:

```python
# From project root
cd adk_test_agent
python -c "from agent import root_agent; print(f'Agent: {root_agent.name}')"
```

### 2. Any Agent Framework Testing

Use the test agent with the Any Agent CLI:

```bash
# Test framework detection
python -m any_agent ./adk_test_agent --dry-run --verbose

# Test with specific framework
python -m any_agent ./adk_test_agent --framework adk --dry-run

# Test full workflow (once implemented)
python -m any_agent ./adk_test_agent --framework adk --build --protocol a2a
```

### 3. MCP Server Setup

If you need MCP functionality, ensure the MCP server is running:

```bash
# Check if MCP server is accessible
curl http://localhost:7081/mcp/health

# Or use environment variable
curl $MCP_SERVER_URL/health
```

## Expected Agent Behavior

### Framework Detection
The Any Agent framework should detect this as a Google ADK agent based on:

- **File Structure**: Presence of `agent.py` and `__init__.py`
- **Imports**: `from google.adk.agents import Agent`
- **Agent Instance**: `root_agent = create_agent()`
- **Dependencies**: ADK-specific packages in requirements.txt

### Agent Capabilities
The test agent provides:

- **MCP Communication**: Can interact with MCP-compatible services
- **DateTime Tools**: Natural language time/date handling
- **Generic Testing**: Validates MCP server connectivity
- **Configurable Models**: Supports different Gemini models

## Development Workflow

### 1. Framework Detection Development

Use this agent to develop and test framework detection:

```python
# Test detection patterns
from any_agent.core.detection import detect_framework
framework = detect_framework("./adk_test_agent")
assert framework.name == "google_adk"
```

### 2. Adapter Development

Use as target for Google ADK adapter:

```python
# Test adapter creation
from any_agent.adapters import GoogleADKAdapter
adapter = GoogleADKAdapter("./adk_test_agent")
agent_instance = adapter.load_agent()
```

### 3. Container Generation Testing

Test Docker container generation:

```bash
# Generate container files
python -m any_agent ./adk_test_agent --framework adk --output ./test_output

# Check generated Dockerfile
cat ./test_output/Dockerfile
```

## Troubleshooting

### Common Issues

#### 1. Missing Google API Key
```
Error: GOOGLE_API_KEY environment variable not set
```
**Solution**: Set `GOOGLE_API_KEY` in your `.env` file

#### 2. MCP Server Not Available
```
Warning: basic_open_agent_tools not available
```
**Solution**: Install optional dependencies or ignore if not needed for testing

#### 3. Import Errors
```
ModuleNotFoundError: No module named 'google.adk'
```
**Solution**: Install Google ADK dependencies:
```bash
pip install google-genai google-adk
```

#### 4. Agent Configuration Issues
```
Agent initialization failed
```
**Solution**: Check environment variables and verify Google API key is valid

### Development Tips

1. **Use Verbose Logging**: Set `LOG_LEVEL=DEBUG` to see detailed agent behavior
2. **Mock MCP Services**: Set `MOCK_EXTERNAL_SERVICES=true` for testing without external dependencies
3. **Test Isolation**: Each test should use a separate agent instance
4. **Configuration Validation**: Always validate environment variables before agent creation

## Integration with Any Agent Framework

This test agent serves as the primary target for:

- **WOB-155**: Google ADK Framework Detection and Adapter Creation
- **WOB-156**: A2A Protocol Implementation for Google ADK
- **WOB-157**: Docker Container Generation for Google ADK Agents
- **WOB-158**: CLI Integration and Testing for Google ADK Support
- **WOB-159**: Helmsman Integration for Google ADK Agents

### Expected Detection Results

The framework should detect:
- **Framework**: `google_adk`
- **Confidence**: `0.95+`
- **Entry Point**: `adk_test_agent/agent.py`
- **Agent Instance**: `root_agent`
- **Dependencies**: Google ADK, MCP tools, datetime tools

### Expected Container Generation

Generated containers should:
- Use Python 3.11 slim base image
- Include all ADK dependencies
- Expose port 8080 (configurable)
- Set proper environment variables
- Include health check endpoint

This setup provides a solid foundation for developing and testing Google ADK integration in the Any Agent framework.