# A2A Python Client Example

This directory contains a simple Python client script that demonstrates how to interact with an A2A (Agent-to-Agent) protocol server.

## Prerequisites

- Python 3.10+
- An A2A server running on `http://localhost:8035/`

## Installation

Install the required dependencies using uv (recommended) or pip:

```bash
# Using uv
uv pip install -r requirements.txt

# Using pip
pip install -r requirements.txt
```

## Usage

Run the client script to connect to your A2A server:

```bash
python a2a_client.py
```

The script will:
1. Connect to the A2A server at `http://localhost:8035/`
2. Fetch the agent card
3. Send a non-streaming message
4. Send a streaming message and display the response chunks

## Configuration

To connect to a different server, modify the `base_url` variable in the `main()` function of `a2a_client.py`.

## Based On

This implementation is based on the A2A Protocol tutorial:
https://a2a-protocol.org/latest/tutorials/python/6-interact-with-server/