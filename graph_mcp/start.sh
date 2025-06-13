#!/bin/bash
set -e

# Navigate to the project directory
cd "$(dirname "$0")"

# Start Neo4j if not running
docker compose up -d neo4j

# Run the MCP server container interactively (replaces any existing one)
exec docker compose run --rm graph-mcp