# Minimal AWS Strands Agent Example

This is a minimal example of an AWS Strands agent using Anthropic Claude Sonnet 4. This agent is designed for framework detection and basic containerization testing without A2A protocol support.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your `.env` file in the project root with:
```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Usage

Run the agent locally:
```bash
python agent.py
```

## Structure

- `__init__.py` - Package initialization, exports `root_agent`
- `agent.py` - Main agent implementation with Anthropic Claude Sonnet 4
- `requirements.txt` - Required dependencies
- `README.md` - This file

## Agent Details

- **Model**: Anthropic Claude Sonnet 4 (`claude-sonnet-4-20250514`)
- **Framework**: AWS Strands
- **Purpose**: Framework detection and basic containerization testing
- **A2A Support**: Not included (minimal implementation)