"""
NeoAlchemy Graph MCP.

FastMCP server for AI integration with Neo4j graph databases.
Provides 11 MCP tools for AI-driven database operations with explicit source tracking.
"""

from .mcp_server import mcp

__all__ = ["mcp"]
