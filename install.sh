#!/bin/bash

# Any Agent - Universal AI Agent Containerization Framework
# Installation Script for macOS, Linux, and Windows (WSL/Git Bash)

set -e

echo "🚀 Installing Any Agent Framework..."
echo

# Check Python version
echo "📋 Checking prerequisites..."
python_version=$(python --version 2>&1 | awk '{print $2}')
required_version="3.10"

if python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
    echo "✅ Python ${python_version} (compatible)"
else
    echo "❌ Python 3.10+ required. Found: ${python_version}"
    echo "   Please upgrade Python and try again."
    exit 1
fi

# Check Docker
if command -v docker &> /dev/null; then
    echo "✅ Docker installed"
else
    echo "⚠️  Docker not found - required for containerization"
    echo "   Install from: https://docs.docker.com/get-docker/"
fi

# Check Node.js for UI features
if command -v node &> /dev/null; then
    node_version=$(node --version 2>/dev/null | cut -d 'v' -f 2 | cut -d '.' -f 1)
    if [ "$node_version" -ge 18 ]; then
        echo "✅ Node.js v$(node --version | cut -d 'v' -f 2) (compatible)"
    else
        echo "⚠️  Node.js 18+ recommended for Chat UI. Found: v$(node --version | cut -d 'v' -f 2)"
    fi
else
    echo "⚠️  Node.js not found - required for Chat UI features"
    echo "   Install from: https://nodejs.org/"
fi

echo

# Install with uv if available, fallback to pip
echo "📦 Installing dependencies..."
if command -v uv &> /dev/null; then
    echo "   Using uv (recommended)..."
    uv sync
    uv pip install -e .
else
    echo "   Using pip..."
    pip install -e ".[dev]"
fi

echo

# Verify installation
echo "🔍 Verifying installation..."
if command -v any-agent &> /dev/null; then
    echo "✅ Installation successful!"
    echo
    echo "🎉 Any Agent is now available system-wide!"
    echo
    echo "   Usage: any-agent ./path/to/agent --port 8080"
    echo "   Help:  any-agent --help"
    echo
    echo "   Alternative: python -m any_agent ./path/to/agent"
    echo
else
    echo "❌ Installation failed - any-agent command not found"
    echo "   Try running: pip install -e ."
    exit 1
fi

# Optional: Install uv if not available
if ! command -v uv &> /dev/null; then
    echo "💡 Tip: Install 'uv' for faster dependency management:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo
fi

echo "📚 Next steps:"
echo "   1. Set up your environment variables (see README.md)"
echo "   2. Try containerizing an example agent:"
echo "      any-agent examples/adk/agent_only --verbose"
echo