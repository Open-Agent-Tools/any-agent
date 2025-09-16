# Generated Dockerfile for Testing_Tessie (Google Adk Agent)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies including uv
RUN apt-get update \
    && apt-get install -y gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*


# Install uv for faster Python package management
RUN pip install --no-cache-dir uv

# Copy requirements and install dependencies  
COPY requirements.txt ./
RUN uv pip install --system --no-cache -r requirements.txt


# Copy agent files
COPY . .

# Copy framework-specific entrypoint script
COPY _adk_entrypoint.py .

# Set default port (can be overridden by environment variable)
ENV AGENT_PORT=8035

# Set framework identifier for A2A client selection
ENV AGENT_FRAMEWORK=google_adk

# Set Google Adk environment variables
ENV GOOGLE_MODEL="gemini-2.0-flash"
ENV GOOGLE_API_KEY=""

# Expose main port
EXPOSE $AGENT_PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$AGENT_PORT/health || exit 1

# Run the framework-specific server
CMD ["sh", "-c", "uv run uvicorn _adk_entrypoint:app --host 0.0.0.0 --port $AGENT_PORT"]
