#!/usr/bin/env python
"""
NeoAlchemy MCP Server - Provides API tools for working with graph data models.

FastMCP server implementation with explicit source chain tracking for complete
data lineage and audit trails. Tools are organized into separate modules by domain.
"""

import os
from dataclasses import dataclass

from fastmcp import FastMCP
from neo4j import GraphDatabase
from neoalchemy import initialize, setup_constraints
from neoalchemy.orm.models import Node, Relationship
from neoalchemy.orm.repository import Neo4jRepository

# Import tool registration functions
from graph_mcp.tools import register_all_tools

# Create a named server
mcp = FastMCP("NeoAlchemy")


@dataclass
class AppContext:
    driver: object  # GraphDatabase driver instance
    repo: Neo4jRepository


# Initialize app context at module level

# Get connection parameters from environment variables
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
repo = Neo4jRepository(driver)

# Initialize field expressions for all models
initialize()

# Setup constraints for registered models
setup_constraints(driver)

# Create app context
app_context = AppContext(driver=driver, repo=repo)

# Access the model registries from the base classes
NODE_MODELS = Node.__registry__
RELATIONSHIP_MODELS = Relationship.__registry__

# Combined model map for all models
MODEL_MAP: dict[str, type[Node] | type[Relationship]] = {
    **NODE_MODELS,
    **RELATIONSHIP_MODELS,
}

# =============================================================================
# REGISTER ALL TOOLS AND RESOURCES
# =============================================================================

# Register all MCP tools and resources
register_all_tools(mcp, app_context, MODEL_MAP)


def main():
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
