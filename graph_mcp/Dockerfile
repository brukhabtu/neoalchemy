# Multi-stage build for graph_mcp with NeoAlchemy wheel
FROM python:3.13-slim AS wheel-builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install UV for building
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/

# Set working directory for NeoAlchemy build
WORKDIR /build

# Copy NeoAlchemy source and config
COPY neoalchemy/ ./neoalchemy/
COPY pyproject.toml uv.lock ./

# Build NeoAlchemy wheel
RUN uv build --wheel

# Runtime stage
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy NeoAlchemy wheel from builder stage
COPY --from=wheel-builder /build/dist/*.whl ./wheels/

# Copy graph_mcp project files
COPY graph_mcp/pyproject.toml ./
COPY graph_mcp/graph_mcp/ ./graph_mcp/

# Install dependencies (no neoalchemy from PyPI), then install our local wheel
RUN uv venv && \
    uv sync --no-install-project && \
    uv pip install ./wheels/*.whl && \
    uv pip install -e .

# Environment variables for external Neo4j connection
ENV NEO4J_URI=bolt://neo4j:7687
ENV NEO4J_USER=neo4j
ENV NEO4J_PASSWORD=password
ENV MCP_LLM_MODEL=claude-3.5-sonnet
ENV PYTHONPATH=/app
WORKDIR /app

# Expose MCP server port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start graph_mcp server
CMD ["uv", "run", "python", "-c", "from graph_mcp.mcp_server import main; main()"]