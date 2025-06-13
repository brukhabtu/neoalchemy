"""
Simplified entity tools for the new architecture.

Extracted from tools_simple.py for clean organization.
"""

from typing import Any

from fastmcp import FastMCP

# Import the organized models and sources

# =============================================================================
# BUSINESS LOGIC IMPLEMENTATIONS
# =============================================================================


async def _create_entity_impl(
    entity_type: str, properties: dict[str, Any], app_context, MODEL_MAP
) -> dict[str, Any]:
    """Create an entity without forced source tracking."""
    if entity_type not in MODEL_MAP:
        available_types = list(MODEL_MAP.keys())
        return {
            "error": f"Unknown entity type: {entity_type}. Available types: {available_types}"
        }

    model_class = MODEL_MAP[entity_type]

    try:
        # Create the entity using Pydantic validation
        entity = model_class.model_validate(properties)

        with app_context.repo.transaction() as tx:
            created_entity = tx.create(entity)

            # Get primary key dynamically
            primary_key = model_class.get_primary_key()
            if primary_key:
                entity_id = getattr(created_entity, primary_key, "unknown")
            else:
                entity_id = "unknown"

            return {
                "success": True,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "entity": created_entity.model_dump(),
                "message": f"Created {entity_type} successfully",
            }

    except Exception as e:
        return {"success": False, "error": f"Failed to create {entity_type}: {str(e)}"}


async def _get_entity_impl(
    entity_type: str, entity_id: str, app_context, MODEL_MAP
) -> dict[str, Any]:
    """Get an entity by its primary key."""
    if entity_type not in MODEL_MAP:
        available_types = list(MODEL_MAP.keys())
        return {
            "error": f"Unknown entity type: {entity_type}. Available types: {available_types}"
        }

    model_class = MODEL_MAP[entity_type]

    try:
        # Use NeoAlchemy's built-in primary key detection
        primary_key = model_class.get_primary_key()
        if not primary_key:
            return {"error": f"No primary key defined for {entity_type}"}

        with app_context.repo.transaction() as tx:
            # Use NeoAlchemy's find_one method with kwargs
            entity = tx.find_one(model_class, **{primary_key: entity_id})

            if not entity:
                return {
                    "error": f"{entity_type} with {primary_key}='{entity_id}' not found"
                }

            return {
                "success": True,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "entity": entity.model_dump(),
            }

    except Exception as e:
        return {"error": f"Failed to get {entity_type}: {str(e)}"}


async def _delete_entity_impl(
    entity_type: str, entity_id: str, app_context, MODEL_MAP
) -> dict[str, Any]:
    """Delete an entity by its primary key."""
    if entity_type not in MODEL_MAP:
        available_types = list(MODEL_MAP.keys())
        return {
            "error": f"Unknown entity type: {entity_type}. Available types: {available_types}"
        }

    model_class = MODEL_MAP[entity_type]

    try:
        # Use NeoAlchemy's built-in primary key detection
        primary_key = model_class.get_primary_key()
        if not primary_key:
            return {"error": f"No primary key defined for {entity_type}"}

        with app_context.repo.transaction() as tx:
            # Use NeoAlchemy's find_one method with kwargs
            entity = tx.find_one(model_class, **{primary_key: entity_id})

            if not entity:
                return {
                    "error": f"{entity_type} with {primary_key}='{entity_id}' not found"
                }

            # Delete the entity (this will also remove relationships)
            tx.delete(entity)

            return {
                "success": True,
                "message": f"Deleted {entity_type} with ID '{entity_id}'",
            }

    except Exception as e:
        return {"error": f"Failed to delete {entity_type}: {str(e)}"}


# =============================================================================
# MCP TOOL REGISTRATION
# =============================================================================


def register_entity_tools(mcp: FastMCP, app_context, MODEL_MAP):
    """Register entity CRUD tools."""

    @mcp.tool()
    async def create_entity(
        entity_type: str, properties: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a new entity with specific properties for each entity type.

        Args:
            entity_type: Type of entity to create. Available types and their required/optional properties:

            Person:
                - email (required): Primary identifier, e.g. "john.doe@company.com"
                - name (required): Full name, e.g. "John Doe"
                - title (optional): Job title, e.g. "Senior Engineer"
                - sources (optional): List of source URIs, e.g. ["ldap://company.com/cn=john.doe"]

            Team:
                - name (required): Team name, e.g. "Platform Team"
                - focus_area (optional): Domain of responsibility, e.g. "Authentication Services"
                - sources (optional): List of source URIs, e.g. ["confluence://company.atlassian.net/spaces/PLAT"]

            Service:
                - name (required): Service name, e.g. "auth-service"
                - description (optional): What the service does
                - url (optional): Primary URL (repository, deployment, documentation)
                - sources (optional): List of source URIs, e.g. ["github://company/auth-service"]

            Task:
                - title (required): Task title or summary, e.g. "Implement user authentication"
                - description (optional): Detailed task description
                - status (optional): One of "todo", "in_progress", "done", "cancelled", "blocked" (default: "todo")
                - priority (optional): Task priority level (free text)
                - assignee (optional): Email of assigned person
                - due_date (optional): Due date (ISO date format)
                - sources (optional): List of source URIs, e.g. ["jira://company.atlassian.net/browse/PROJ-123"]

            Document:
                - title (required): Document title, e.g. "API Documentation"
                - url (optional): URL to original document
                - sources (optional): List of source URIs, e.g. ["confluence://company.atlassian.net/pages/123456"]

            properties: Dictionary with the specific properties for the chosen entity_type (see above)

        Returns:
            Dictionary containing the created entity data with 'success' field
        """
        return await _create_entity_impl(
            entity_type, properties, app_context, MODEL_MAP
        )

    @mcp.tool()
    async def get_entity(entity_type: str, entity_id: str) -> dict[str, Any]:
        """Get an entity by its primary key.

        Args:
            entity_type: Type of entity to retrieve
            entity_id: Primary key value of the entity

        Returns:
            Dictionary containing the entity data with 'success' field
        """
        return await _get_entity_impl(entity_type, entity_id, app_context, MODEL_MAP)

    @mcp.tool()
    async def delete_entity(entity_type: str, entity_id: str) -> dict[str, Any]:
        """Delete an entity by its primary key.

        Args:
            entity_type: Type of entity to delete
            entity_id: Primary key value of the entity

        Returns:
            Dictionary confirming deletion with 'success' field
        """
        return await _delete_entity_impl(entity_type, entity_id, app_context, MODEL_MAP)

