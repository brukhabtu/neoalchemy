FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    npm \
    git \
    wget \
    pipx \ 
    ca-certificates \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g @anthropic-ai/claude-code --no-fund --no-audit

# Create a non-root user
RUN groupadd --gid 1000 devuser \
    && useradd --uid 1000 --gid 1000 -m devuser \
    && mkdir -p /app \
    && chown -R devuser:devuser /app

# Install uv package manager and add it to PATH
USER devuser
RUN pipx install uv
ENV PATH="/home/devuser/.local/bin:$PATH"
RUN uv --version

# Set up working directory
WORKDIR /app

# Create default project structure
RUN mkdir -p /app/src

# Create virtual environment
ENV VIRTUAL_ENV=/app/.venv
RUN uv venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# We'll use the user's existing pyproject.toml and uv.lock
COPY --chown=devuser:devuser pyproject.toml uv.lock /app/

# Install Python dependencies using uv with the lock file into the venv
RUN uv pip install -e ".[dev]" 

CMD ["sleep", "infinity"]
