FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN groupadd --gid 1000 testuser \
    && useradd --uid 1000 --gid 1000 -m testuser

# Install uv package manager
USER testuser
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/testuser/.local/bin:$PATH"

# Set up working directory
WORKDIR /workspace
USER root
RUN chown -R testuser:testuser /workspace
USER testuser

# Create virtual environment first
RUN uv venv /workspace/.venv
ENV PATH="/workspace/.venv/bin:$PATH"

# Copy the entire project
COPY --chown=testuser:testuser . /workspace/

# Install dependencies and project in development mode
RUN uv pip install -e ".[dev]"

# Default command runs unit tests
CMD ["python", "-m", "pytest", "tests/unit/", "-v"]