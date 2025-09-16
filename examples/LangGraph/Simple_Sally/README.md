# Simple Sally - LangGraph Agent

A minimal LangGraph agent demonstrating stateful, graph-based agent patterns with memory and tools. Designed as a 2025 starter example following modern LangGraph best practices.

## Features

- **Stateful Conversations**: Memory persistence across interactions
- **Graph-Based Architecture**: Built on LangGraph's state graph framework
- **Tool Integration**: Weather, Calculator, Time, and Memory tools
- **Thread-Based Sessions**: Separate conversation threads with unique IDs
- **Streaming Support**: Real-time response streaming

## Tools Available

1. **Weather**: Get weather for any city
2. **Calculator**: Perform basic mathematical calculations
3. **Time**: Get current date and time
4. **Remember Info**: Store information for later use in conversation

## Architecture

```
Simple Sally (LangGraph Agent)
├── Language Model: GPT-4o-mini
├── Framework: LangGraph ReAct Agent
├── Memory: MemorySaver (stateful conversations)
├── Threading: Separate conversation threads
└── Tools: [Weather, Calculator, Time, Memory]
```

## Key Differences from LangChain

- **State Management**: Automatic state persistence across turns
- **Memory**: Built-in conversation memory with thread IDs
- **Streaming**: Native streaming support for real-time responses
- **Graph Structure**: Nodes and edges for complex workflows
- **Checkpointing**: Automatic state checkpointing

## Usage

```python
from agent import create_agent

# Create agent
agent = create_agent()

# Run with thread ID for conversation continuity
config = {"configurable": {"thread_id": "user123"}}
response = agent.invoke(
    {"messages": [{"role": "user", "content": "Remember that I like pizza"}]},
    config
)

# Continue conversation in same thread
response2 = agent.invoke(
    {"messages": [{"role": "user", "content": "What do I like to eat?"}]},
    config
)
```

## Example Interactions

```
User: "Remember that I live in Boston"
Sally: Uses Remember tool → "I'll remember: I live in Boston"

User: "What's the weather where I live?"
Sally: Recalls Boston from memory → Uses Weather tool → "The weather in Boston is sunny and 72°F."

User: "Calculate 25 * 8"
Sally: Uses Calculator tool → "The result of 25 * 8 is 200"
```

## Conversation Threads

Each conversation can have a unique thread ID:

```python
# User A's conversation
config_a = {"configurable": {"thread_id": "user_a"}}
agent.invoke({"messages": [{"role": "user", "content": "I'm 25 years old"}]}, config_a)

# User B's conversation (separate memory)
config_b = {"configurable": {"thread_id": "user_b"}}
agent.invoke({"messages": [{"role": "user", "content": "I'm 30 years old"}]}, config_b)
```

## Requirements

- OpenAI API key in environment or `.env` file
- `langgraph`, `langchain-openai`, `python-dotenv`

## Configuration

Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-key-here"
```

Or create a `.env` file:
```
OPENAI_API_KEY=your-key-here
```

## Future Migration

Note: LangGraph v1.0 is coming in October 2025, which may introduce API changes. This example follows current best practices for the transition period.