# Generic A2A Client Design

## Status: ✅ Validated (Fully functional)
**Last Updated**: September 1, 2025 - Post Chat UI Enhancement  
**Implementation**: Tested and verified with Google ADK and AWS Strands agents  
**Multi-turn Context**: ✅ Implemented and validated with conversation state preservation  
**Session Isolation**: ✅ Complete A2A session isolation implemented and validated  
**Chat UI Integration**: ✅ Both frameworks working with enhanced response extraction

### 🎉 Recent Enhancements (September 1, 2025)
- **ADK Chat UI Fix**: Resolved "Task completed: Task" fallback messages through proper `task.status.message.parts` extraction
- **Context Wrapper Optimization**: ADK agents bypass unnecessary wrapper (native A2A context isolation)
- **Framework-Specific Response Handling**: Enhanced extraction patterns for both ADK and Strands response structures
- **Production Validation**: Both frameworks now provide meaningful responses in Chat UI interface

## Overview

This document provides a comprehensive guide for creating and interacting with A2A (Agent-to-Agent) protocol clients using the official `a2a-sdk` library. The patterns described here have been validated against production agents and follow official documentation from Context7.

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [Client Architecture](#client-architecture)
3. [Implementation Guide](#implementation-guide)
4. [Multi-turn Conversation Context](#multi-turn-conversation-context)
5. [A2A Session Isolation](#a2a-session-isolation)
6. [Best Practices](#best-practices)
7. [Response Handling](#response-handling)
8. [Error Management](#error-management)
9. [Testing Patterns](#testing-patterns)
10. [Framework Compatibility](#framework-compatibility)

## Core Concepts

### Agent-to-Agent (A2A) Protocol
The A2A protocol enables standardized communication between AI agents regardless of their underlying implementation framework. Key characteristics:

- **Protocol Agnostic**: Works with Google ADK, AWS Strands, LangChain, CrewAI, and other frameworks
- **Asynchronous**: Built on async/await patterns for non-blocking communication
- **Streaming Support**: Handles both single responses and streaming message flows
- **Type Safety**: Comprehensive type hints and validation throughout

### Key Components
- **Agent Card**: Metadata describing agent capabilities, protocols, and endpoints
- **Client Factory**: Official pattern for creating framework-agnostic clients
- **Message Objects**: Structured communication format with role-based validation
- **Response Handlers**: Processing streaming and single-shot agent responses

## Client Architecture

### Official SDK Pattern
```python
# Core imports following official documentation
from a2a.client import ClientFactory, A2ACardResolver, ClientConfig
from a2a.client.helpers import create_text_message_object
from a2a.types import Role
import httpx
import asyncio
```

### Component Relationships
```
httpx.AsyncClient
    ↓
A2ACardResolver → Agent Card
    ↓
ClientConfig → ClientFactory → A2A Client
    ↓
create_text_message_object → Message
    ↓
client.send_message() → Response Iterator
```

## Implementation Guide

### Step 1: Environment Setup

```python
#!/usr/bin/env python3
"""
A2A Client Implementation
"""
import asyncio
import httpx
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

### Step 2: Import Official Components

```python
# CRITICAL: Use only official a2a-sdk imports
from a2a.client import ClientFactory, A2ACardResolver, ClientConfig
from a2a.client.helpers import create_text_message_object
from a2a.types import Role
```

### Step 3: Agent Discovery and Client Creation

```python
async def create_a2a_client(base_url: str, httpx_client: httpx.AsyncClient):
    """Create an A2A client using official patterns."""
    
    # Step 3.1: Fetch Agent Card using A2ACardResolver
    logger.info(f"Fetching agent card from: {base_url}")
    resolver = A2ACardResolver(
        httpx_client=httpx_client,
        base_url=base_url
    )
    agent_card = await resolver.get_agent_card()
    logger.info(f"✅ Agent card retrieved: {agent_card.name}")
    
    # Step 3.2: Create ClientConfig with httpx_client
    client_config = ClientConfig(httpx_client=httpx_client)
    
    # Step 3.3: Create ClientFactory
    factory = ClientFactory(config=client_config)
    
    # Step 3.4: Create client using factory.create(card)
    client = factory.create(card=agent_card)
    logger.info(f"✅ A2A client created: {type(client)}")
    
    return client, agent_card
```

### Step 4: Message Creation and Sending

```python
async def send_message_to_agent(client, message_content: str):
    """Send message using official helper functions."""
    
    # Step 4.1: Create message using official helper
    message = create_text_message_object(
        role=Role.user,  # CRITICAL: Use Role.user for user messages
        content=message_content
    )
    logger.info("✅ Message created with official helper")
    
    # Step 4.2: Send message using client.send_message()
    responses = []
    final_response = None
    
    # Official pattern: client.send_message returns AsyncIterator
    async for response in client.send_message(message):
        logger.info(f"📨 Received response type: {type(response)}")
        
        # Track response metadata
        response_type = response.__class__.__name__ if hasattr(response, '__class__') else str(type(response))
        responses.append({
            "type": response_type,
            "timestamp": asyncio.get_running_loop().time()
        })
        
        # Extract response data using model_dump
        if hasattr(response, 'model_dump'):
            response_data = response.model_dump(mode='json', exclude_none=True)
            logger.info(f"📋 Response data keys: {list(response_data.keys())}")
            
            # Extract agent response from artifacts or message parts
            if 'artifacts' in response_data:
                for artifact in response_data.get('artifacts', []):
                    for part in artifact.get('parts', []):
                        if 'text' in part:
                            final_response = part['text']
                            logger.info(f"🤖 Agent response: {part['text'][:150]}...")
                            break
            elif 'parts' in response_data:
                for part in response_data.get('parts', []):
                    if 'text' in part:
                        final_response = part['text']
                        logger.info(f"💬 Message response: {part['text'][:150]}...")
                        break
        else:
            logger.info(f"📄 Raw response: {str(response)[:200]}...")
    
    return {
        "responses_count": len(responses),
        "response_types": [r["type"] for r in responses],
        "final_response": final_response,
        "status": "success"
    }
```

### Step 5: Complete Client Implementation

```python
async def interact_with_a2a_agent(base_url: str, message_content: str) -> Dict[str, Any]:
    """Complete A2A client interaction following official patterns."""
    
    results = {
        "base_url": base_url,
        "agent_card": None,
        "a2a_client": None,
        "message_response": None,
        "errors": []
    }
    
    async with httpx.AsyncClient() as httpx_client:
        try:
            # Create client
            client, agent_card = await create_a2a_client(base_url, httpx_client)
            
            # Store agent card metadata
            results["agent_card"] = {
                "name": agent_card.name,
                "description": agent_card.description,
                "protocol_version": getattr(agent_card, 'protocol_version', 'unknown')
            }
            
            results["a2a_client"] = {
                "status": "created", 
                "type": str(type(client))
            }
            
            # Send message
            message_response = await send_message_to_agent(client, message_content)
            results["message_response"] = message_response
            
            # Close client
            await client.close()
            logger.info("✅ A2A client closed")
            
        except Exception as e:
            error_msg = f"A2A SDK operations failed: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
    
    return results


# Usage example
async def main():
    """Example usage of A2A client."""
    base_url = "http://localhost:8035"
    message = "Hello from A2A client! Can you confirm receipt?"
    
    results = await interact_with_a2a_agent(base_url, message)
    print(f"Results: {results}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Multi-turn Conversation Context

### Overview
Multi-turn conversation context preservation is essential for building chatbot-style interactions where agents need to remember information from previous messages in a conversation session. The A2A protocol provides native support for this through context identifiers.

### Core Context Fields

The A2A Message object supports three key context fields for maintaining conversation state:

```python
from a2a.client.helpers import create_text_message_object
from a2a.types import Role

# Create message with context preservation
message = create_text_message_object(
    role=Role.user,
    content="What is my name?"
)

# Set context fields (snake_case naming)
message.context_id = "session_abc123"              # Primary session identifier
message.reference_task_ids = ["task_xyz789"]       # Reference previous tasks
# Note: parent_message_id handled via message metadata
```

### Context Field Descriptions

| Field | Purpose | Format | Example |
|-------|---------|--------|---------|
| `context_id` | Groups related messages/tasks within a session | String UUID | `"session_abc123"` |
| `reference_task_ids` | Lists previous task IDs to provide context hints | List of strings | `["task_xyz789", "task_def456"]` |

### Implementation Pattern

#### Unified A2A Client with Context Support

```python
from typing import Optional, List
from a2a.client import ClientFactory, A2ACardResolver, ClientConfig
from a2a.client.helpers import create_text_message_object
from a2a.types import Role
import httpx

class UnifiedA2AClientHelper:
    """A2A client with multi-turn conversation support."""
    
    async def send_message(
        self,
        agent_url: str, 
        message_content: str,
        context_id: Optional[str] = None,
        reference_task_ids: Optional[List[str]] = None,
        parent_message_id: Optional[str] = None
    ) -> List[str]:
        """Send message with conversation context preservation.
        
        Args:
            agent_url: URL of the A2A agent
            message_content: User message content
            context_id: Session identifier for context continuity
            reference_task_ids: Previous task IDs for context
            parent_message_id: Previous message ID (for future use)
        """
        async with httpx.AsyncClient(timeout=30) as httpx_client:
            # Step 1: Create A2A client
            client, agent_card = await self._create_a2a_client(agent_url, httpx_client)
            
            try:
                # Step 2: Create message with context
                message = create_text_message_object(
                    role=Role.user,
                    content=message_content
                )
                
                # Step 3: Add context fields for conversation continuity
                if context_id:
                    message.context_id = context_id
                
                if reference_task_ids:
                    message.reference_task_ids = reference_task_ids
                
                # Step 4: Send message and process responses
                agent_responses = []
                async for response in client.send_message(message):
                    response_text = self._extract_response_content(response)
                    if response_text:
                        agent_responses.append(response_text)
                
                return agent_responses
                
            finally:
                await client.close()
```

#### Session Management Integration

```python
class ChatHandler:
    """Chat handler with session-aware A2A client integration."""
    
    async def send_message(self, session_id: str, message_content: str):
        # Prepare context for multi-turn conversation
        context_id = session_id  # Use session ID as context ID
        parent_message_id = None
        reference_task_ids = []
        
        # Extract parent message from session history
        session = self.sessions[session_id]
        if len(session.messages) > 1:
            prev_msg = session.messages[-2]  # Previous message
            parent_message_id = prev_msg.id
        
        # Send message with context preservation
        agent_responses = await self.a2a_client.send_message(
            session.agent_url,
            message_content,
            context_id=context_id,
            reference_task_ids=reference_task_ids,
            parent_message_id=parent_message_id
        )
        
        return agent_responses
```

### Testing Context Preservation

#### Validation Test Pattern

```python
async def test_multi_turn_context():
    """Test that agent maintains conversation context."""
    client = UnifiedA2AClientHelper()
    context_id = "test_session_123"
    
    # Step 1: Establish context
    responses1 = await client.send_message(
        "http://localhost:8035", 
        "my name is Alex",
        context_id=context_id
    )
    print(f"Response 1: {responses1[0]}")
    
    # Step 2: Test context retention
    responses2 = await client.send_message(
        "http://localhost:8035",
        "what is my name?", 
        context_id=context_id  # Same context_id
    )
    print(f"Response 2: {responses2[0]}")
    
    # Validation: Response should contain "alex"
    assert "alex" in responses2[0].lower(), "Agent failed to retain context"
    print("✅ Context preservation test passed!")
```

### Framework Compatibility

| Framework | Context Support | Session Isolation | Notes |
|-----------|----------------|------------------|-------|
| Google ADK | ✅ Full | ✅ Complete | Native A2A Task Manager with contextId and session isolation |
| AWS Strands | ✅ Full | ✅ Complete | Streaming context with FileSessionManager isolation |
| LangChain | ✅ Partial | ✅ Complete | Framework upgrade provides full session isolation |
| CrewAI | ⚠️ Limited | ✅ Complete | Framework upgrade enables session isolation |

### Best Practices for Context

1. **Use Session IDs as Context IDs**: Map your application session identifiers directly to A2A `context_id` fields
2. **Consistent Context Application**: Always use the same `context_id` for all messages within a conversation session
3. **Reference Task Tracking**: Store and pass `task_id` values from agent responses as `reference_task_ids` in follow-up messages
4. **Context Validation**: Test multi-turn scenarios to ensure agents retain conversation state
5. **Fallback Handling**: Implement graceful degradation when agents don't support context preservation

## A2A Session Isolation

### Status: ✅ Fully functional
**Implementation**: Completed September 1, 2025  
**Validation**: Full session isolation verified across multiple concurrent conversations

### Overview

Session isolation ensures that multiple concurrent A2A conversations maintain completely separate context states, preventing context bleeding where information from one session appears in another. This is critical for multi-user applications and concurrent chat sessions.

### The Context Bleeding Problem

**Problem**: Without proper session isolation, agents may share conversation history across different `context_id` values, leading to:
- User A's messages appearing in User B's conversation 
- Shared conversation state across separate chat sessions
- Security and privacy violations in multi-tenant environments

**Root Cause**: Many agent frameworks don't natively respect A2A `context_id` fields, using global conversation history instead of per-context isolation.

### Solution Architecture

#### Context-Aware Agent Wrapper System

The Any Agent framework provides automatic session isolation through a pipeline-level upgrade system:

```python
# Context-aware wrapper automatically applied during containerization
from any_agent.core.context_aware_wrapper import upgrade_agent_for_context_isolation

# Automatic framework detection and context isolation
upgraded_agent = upgrade_agent_for_context_isolation(original_agent)
```

#### Framework-Specific Isolation Strategies

| Framework | Isolation Method | Implementation |
|-----------|-----------------|----------------|
| **AWS Strands** | FileSessionManager per context_id | Uses Strands' built-in session management |
| **Google ADK** | Task isolation via context routing | Context-aware task management |
| **Generic** | Separate agent instances per context_id | Instance isolation for other frameworks |

#### A2A Server Integration

Custom A2A server executor extracts `context_id` from incoming messages and routes to isolated agent instances:

```python
class ContextAwareStrandsA2AExecutor(StrandsA2AExecutor):
    async def _execute_streaming(self, context: RequestContext, updater):
        # Extract context_id from A2A RequestContext
        context_id = context.context_id
        
        # Route to context-isolated agent instance
        if hasattr(self.agent, '_context_aware_wrapper'):
            result = self.agent(user_input, context_id=context_id)
        else:
            # Fallback to original behavior
            result = self.agent(user_input)
```

### Implementation Details

#### 1. Automatic Pipeline Upgrade

All agents deployed through Any Agent automatically receive context isolation:

```bash
# Context isolation applied automatically
python -m any_agent ./my_strands_agent --port 8080
```

#### 2. Context Extraction and Routing

The system extracts `context_id` from A2A messages and creates isolated agent instances:

```python
# Example: Strands agents get separate FileSessionManager per context_id
session_manager = FileSessionManager(
    session_id=context_id,
    storage_dir=temp_dir
)

context_agent = Agent(
    model=base_agent.model,
    system_prompt=base_agent.system_prompt,
    session_manager=session_manager  # Isolated session
)
```

#### 3. Thread-Safe Session Management

The context wrapper uses thread-safe patterns for concurrent session handling:

```python
class ContextAwareWrapper:
    def __init__(self, base_agent):
        self.context_agents = {}  # context_id -> isolated_agent
        self.lock = threading.RLock()  # Thread safety
    
    def _get_agent_for_context(self, context_id):
        with self.lock:
            if context_id not in self.context_agents:
                self.context_agents[context_id] = self._create_isolated_agent()
```

### Validation Testing

#### Session Isolation Test Pattern

```python
# Test: Create 3 concurrent sessions with different names
sessions = {
    "alice": "my name is alice",
    "bob": "my name is bob", 
    "charlie": "my name is charlie"
}

# Each session introduces different name
for name, message in sessions.items():
    response = await send_a2a_message(message, context_id=f"session_{name}")

# Validation: Each session should only remember its own name
for name in sessions:
    response = await send_a2a_message("what is my name?", context_id=f"session_{name}")
    assert name.lower() in response.lower()
    assert other_names not in response.lower()  # No context bleeding
```

#### Test Results

```
🔒 Session Isolation Test
==================================================
✅ alice session: Agent correctly remembered 'alice'
✅ bob session: Agent correctly remembered 'bob'  
✅ charlie session: Agent correctly remembered 'charlie'

🎉 Session isolation test PASSED!
✅ Context is properly isolated between sessions
```

### Framework Compatibility

| Framework | Session Isolation | Implementation Status | Notes |
|-----------|------------------|----------------------|--------|
| **AWS Strands** | ✅ Complete | Fully functional | Uses FileSessionManager per context_id |
| **Google ADK** | ✅ Complete | Fully functional | Context-aware task routing |
| **LangChain** | ✅ Supported | Framework Upgrade | Separate chain instances per context |
| **CrewAI** | ✅ Supported | Framework Upgrade | Isolated crew instances |
| **Generic** | ✅ Supported | Framework Upgrade | Instance isolation pattern |

### Production Benefits

1. **Privacy & Security**: Complete separation of user conversations
2. **Multi-tenancy**: Safe concurrent access for multiple users  
3. **Scalability**: Isolated context scales with concurrent sessions
4. **Transparency**: Works with existing agents via automatic upgrade
5. **Performance**: Efficient context routing with minimal overhead

### Best Practices for Session Isolation

1. **Always Use Context IDs**: Include unique `context_id` in every A2A message
2. **Session Mapping**: Map application session IDs directly to A2A context_id values
3. **Validation Testing**: Test concurrent sessions to verify no context bleeding
4. **Context Cleanup**: Consider cleanup strategies for long-running applications
5. **Monitoring**: Log context_id routing for debugging and analytics

## Best Practices

### 1. Official SDK Imports Only
```python
# ✅ CORRECT - Official SDK imports
from a2a.client import ClientFactory, A2ACardResolver, ClientConfig
from a2a.client.helpers import create_text_message_object
from a2a.types import Role

# ❌ INCORRECT - Custom HTTP implementations
import requests
import json
```

### 2. Proper Resource Management
```python
# ✅ CORRECT - Use async context managers
async with httpx.AsyncClient() as httpx_client:
    # ... client operations
    await client.close()  # Always close the client

# ❌ INCORRECT - Manual resource management
httpx_client = httpx.AsyncClient()
# ... operations without proper cleanup
```

### 3. Role-Based Message Creation
```python
# ✅ CORRECT - Use Role enum
from a2a.types import Role
message = create_text_message_object(
    role=Role.user,
    content="User message content"
)

# ❌ INCORRECT - String literals
message = create_text_message_object(
    role="user",  # This will cause validation errors
    content="User message content"
)
```

### 4. Comprehensive Error Handling
```python
try:
    client, agent_card = await create_a2a_client(base_url, httpx_client)
except httpx.HTTPError as e:
    logger.error(f"HTTP error during agent discovery: {e}")
except ImportError as e:
    logger.error(f"a2a-sdk not properly installed: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

## Response Handling

### Understanding Response Types

Different agent frameworks return different response patterns:

#### Google ADK Agents
- **Response Count**: Typically 1 response
- **Response Type**: Single tuple with complete task information
- **Artifacts**: Contains text parts with agent response

#### AWS Strands Agents  
- **Response Count**: Multiple responses (e.g., 15 streaming responses)
- **Response Type**: Stream of tuples representing incremental updates
- **Artifacts**: Progressive updates to the agent's thinking process

### Response Processing Pattern
```python
async for response in client.send_message(message):
    if hasattr(response, 'model_dump'):
        response_data = response.model_dump(mode='json', exclude_none=True)
        
        # Process artifacts (primary response location)
        for artifact in response_data.get('artifacts', []):
            for part in artifact.get('parts', []):
                if 'text' in part:
                    agent_text = part['text']
                    # Process agent response
                    
        # Fallback: process direct message parts
        for part in response_data.get('parts', []):
            if 'text' in part:
                message_text = part['text']
                # Process message content
```

## Error Management

### Common Error Scenarios

1. **Import Errors**
   ```python
   # a2a-sdk not installed or incompatible version
   ImportError: cannot import name 'MessagePart' from 'a2a.types'
   ```

2. **Connection Errors**
   ```python
   # Agent not running or incorrect URL
   httpx.ConnectError: [Errno 61] Connection refused
   ```

3. **Validation Errors**
   ```python
   # Incorrect role specification
   ValidationError: 1 validation error for Message\nrole\nInput should be 'agent' or 'user'
   ```

### Error Handling Strategy
```python
def handle_a2a_errors(func):
    """Decorator for comprehensive A2A error handling."""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ImportError as e:
            if "a2a" in str(e):
                logger.error("a2a-sdk not properly installed. Run: pip install a2a-sdk")
            raise
        except httpx.ConnectError as e:
            logger.error(f"Cannot connect to agent. Ensure agent is running at {args[0] if args else 'specified URL'}")
            raise
        except Exception as e:
            logger.error(f"Unexpected A2A error: {e}")
            raise
    return wrapper
```

## Testing Patterns

### Multi-Agent Testing
```python
async def test_multiple_agents():
    """Test pattern for multiple agent endpoints."""
    agents = [
        "http://localhost:8035",  # Google ADK agent
        "http://localhost:8045",  # AWS Strands agent
    ]
    
    results = {}
    for agent_url in agents:
        logger.info(f"Testing {agent_url}...")
        results[agent_url] = await interact_with_a2a_agent(
            agent_url, 
            "Test message for multi-agent validation"
        )
    
    return results
```

### Validation Testing
```python
def validate_agent_response(results: Dict[str, Any]) -> bool:
    """Validate that agent interaction was successful."""
    required_fields = ["agent_card", "a2a_client", "message_response"]
    
    for field in required_fields:
        if not results.get(field):
            return False
    
    if results.get("errors"):
        return False
        
    message_response = results.get("message_response", {})
    return message_response.get("status") == "success"
```

## Framework Compatibility

### Validated Frameworks

| Framework | Status | Response Pattern | Notes |
|-----------|--------|------------------|-------|
| Google ADK | ✅ Production + Chat UI | Single response | Uses MCP for external services, **Chat UI enhanced Sept 2025** |
| AWS Strands | ✅ Production + Chat UI | Streaming (15+ responses) | Anthropic Claude Sonnet 4, **Session isolation complete** |
| LangChain | 🧪 Testing | TBD | Adapter completed |
| CrewAI | 🧪 Testing | TBD | Adapter completed |

### Framework-Specific Considerations

#### Google ADK
- Environment: `GOOGLE_API_KEY`, `GOOGLE_MODEL`, `MCP_SERVER_URL`
- Response: Single comprehensive response with complete task information
- Port: Typically 8035

#### AWS Strands  
- Environment: `ANTHROPIC_API_KEY`
- Response: Progressive streaming responses showing agent thinking process
- Port: Typically 8045

## Security Considerations

### Authentication
```python
# Environment variables should be properly loaded
import os
from pathlib import Path

def load_environment():
    """Load environment variables with proper precedence."""
    # Priority: CLI args > agent folder .env > current directory .env
    env_files = [
        Path.cwd() / ".env",
        Path("agent_directory") / ".env"
    ]
    
    for env_file in env_files:
        if env_file.exists():
            # Load environment file
            break
    else:
        raise RuntimeError("No .env file found - authentication will fail")
```

### Agent Trust Model
From the A2A samples repository documentation:
> "When building production applications, it is critical to treat any agent operating outside of your direct control as a potentially untrusted entity."

Key security practices:
- Validate all agent responses before processing
- Implement timeouts for agent communications
- Log all agent interactions for audit purposes
- Use environment variables for sensitive credentials
- Never hardcode API keys or authentication tokens

## Troubleshooting Guide

### Common Issues and Solutions

1. **"cannot import name 'MessagePart' from 'a2a.types'"**
   - **Cause**: Incompatible a2a-sdk version
   - **Solution**: Update to latest version: `pip install --upgrade a2a-sdk`

2. **"Connection refused" errors**  
   - **Cause**: Agent not running or wrong port
   - **Solution**: Verify agent status with `docker ps` or check agent logs

3. **"1 validation error for Message\nrole"**
   - **Cause**: Using string literal instead of Role enum
   - **Solution**: Import `from a2a.types import Role` and use `Role.user`

4. **Empty or null responses**
   - **Cause**: Agent processing errors or misconfiguration  
   - **Solution**: Check agent logs and environment variables

5. **Timeout errors**
   - **Cause**: Agent taking too long to respond
   - **Solution**: Increase httpx client timeout or check agent performance

### Debug Logging
```python
# Enable detailed debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Log all HTTP requests
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.DEBUG)
```

## Task Cancellation Support

### Overview ✅ Fully functional (WOB-173)
**Status**: Completed September 10, 2025  
**Implementation**: Full cancel method support for ContextAwareStrandsA2AExecutor

The AWS Strands A2A executor now supports graceful task cancellation through the `cancel()` method, enabling clients to interrupt long-running agent operations.

### Cancel Method Implementation

The `ContextAwareStrandsA2AExecutor` implements the A2A protocol cancel method with the following signature:

```python
async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
    """Cancel an ongoing execution.
    
    This method gracefully cancels a running agent task by:
    1. Logging the cancellation request
    2. Attempting to stop any ongoing agent operations
    3. Sending a cancellation message to the event queue
    4. Handling edge cases (no active task, already completed task)
    
    Args:
        context: The A2A request context containing task information
        event_queue: The A2A event queue for sending cancellation events
        
    Raises:
        No exceptions - gracefully handles all cancellation scenarios
    """
```

### Cancellation Features

#### Graceful Task Termination
- **Active Task Detection**: Verifies if there's an active task to cancel
- **State Validation**: Checks if task is already in final state (completed, cancelled, failed)
- **Context Cleanup**: Removes context-specific agent instances for memory management

#### Error Handling
- **Exception Safety**: Never raises exceptions, always handles errors gracefully
- **Event Queue Integration**: Sends status messages to the A2A event queue
- **Logging**: Comprehensive logging for debugging and monitoring

#### Context-Aware Cancellation
- **Context Isolation**: Cleans up context-specific agent instances when available
- **Session Management**: Removes isolated agent sessions to prevent resource leaks
- **Thread Safety**: Safe concurrent access to context management structures

### Usage Example

```python
# The cancel method is called automatically by A2A protocol infrastructure
# when a client requests task cancellation

# Example of how a client might trigger cancellation:
# 1. Client sends cancellation request to A2A server
# 2. A2A server calls executor.cancel(context, event_queue)
# 3. Cancel method gracefully terminates the agent task
# 4. Client receives cancellation confirmation via event queue
```

### Cancellation Scenarios Handled

| Scenario | Behavior |
|----------|----------|
| **Active Task** | Graceful termination with confirmation message |
| **No Active Task** | Returns "No active task to cancel" message |
| **Already Completed** | Returns "Task already completed, cannot cancel" |
| **Already Cancelled** | Returns "Task already cancelled, cannot cancel" |
| **Context-Aware Agent** | Cleans up context-specific instances |
| **Exception During Cancel** | Logs error and sends fallback cancellation message |

### Test Coverage

The cancel method includes comprehensive test coverage with 11 test cases:

- Method signature validation
- Active task cancellation
- No active task handling
- Already completed/cancelled task scenarios
- Context-aware agent cleanup
- Exception handling
- Logging verification
- Task ID inclusion in messages

### Production Benefits

1. **Responsive User Experience**: Users can cancel long-running operations
2. **Resource Management**: Prevents runaway tasks from consuming resources
3. **Memory Efficiency**: Cleans up context-specific agent instances
4. **Reliability**: Graceful error handling prevents system instability
5. **Monitoring**: Comprehensive logging for operational visibility

## Conclusion

This design document provides a Fully functional pattern for A2A client implementation that has been validated against multiple agent frameworks. The key success factors are:

1. **Official SDK Usage**: Strict adherence to documented patterns
2. **Proper Resource Management**: Async context managers and client lifecycle
3. **Comprehensive Error Handling**: Graceful degradation and meaningful error messages  
4. **Framework Agnostic**: Works across Google ADK, AWS Strands, and other frameworks
5. **Security Conscious**: Proper authentication and environment management
6. **Task Cancellation**: Graceful task termination with comprehensive error handling

For implementation questions or framework-specific guidance, refer to the working example in `tmp/test_official_a2a_sdk.py` which demonstrates all patterns described in this document.