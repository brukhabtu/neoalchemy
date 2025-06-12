"""
MCP tools package for the simplified graph MCP architecture.

This package organizes MCP tools into logical modules:
- entities.py: Entity CRUD operations (Person, Team, Service, Task, Document)
- relationships.py: Business relationship operations
- query.py: Flexible querying capabilities
- schemas.py: Schema discovery resources

Source tracking is now handled via URI-based sources fields in each entity.
"""

from graph_mcp.tools.entities import register_entity_tools
from graph_mcp.tools.query import register_query_tools
from graph_mcp.tools.relationships import register_relationship_tools
from graph_mcp.tools.schemas import register_schema_resources


def register_all_tools(mcp, app_context, MODEL_MAP):
    """Register all MCP tools and resources."""
    register_entity_tools(mcp, app_context, MODEL_MAP)
    register_relationship_tools(mcp, app_context, MODEL_MAP)
    register_query_tools(mcp, app_context, MODEL_MAP)
    register_schema_resources(mcp)


__all__ = [
    "register_entity_tools",
    "register_relationship_tools",
    "register_query_tools",
    "register_schema_resources",
    "register_all_tools",
]
