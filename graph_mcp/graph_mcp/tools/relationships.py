"""
Relationship tools using NeoAlchemy's built-in methods.

Handles business relationship creation and management using proper
NeoAlchemy APIs instead of reinventing primary key detection.
"""

from typing import Any

from fastmcp import FastMCP

# Import the simplified relationships
from graph_mcp.models import DEPENDS_ON, MEMBER_OF, REFERENCES, RESPONSIBLE_FOR, WORKS_ON

# =============================================================================
# BUSINESS LOGIC IMPLEMENTATIONS
# =============================================================================


async def _create_relationship_impl(
    relationship_type: str,
    from_entity_type: str,
    from_entity_id: str,
    to_entity_type: str,
    to_entity_id: str,
    properties: dict[str, Any] | None,
    app_context,
    MODEL_MAP,
) -> dict[str, Any]:
    """Create a relationship between two entities using NeoAlchemy's built-in methods."""
    # Validate entity types
    if from_entity_type not in MODEL_MAP or to_entity_type not in MODEL_MAP:
        return {"error": f"Invalid entity types. Available: {list(MODEL_MAP.keys())}"}

    from_model_class = MODEL_MAP[from_entity_type]
    to_model_class = MODEL_MAP[to_entity_type]

    # Map relationship types to classes
    relationship_map = {
        "MEMBER_OF": MEMBER_OF,
        "RESPONSIBLE_FOR": RESPONSIBLE_FOR,
        "WORKS_ON": WORKS_ON,
        "DEPENDS_ON": DEPENDS_ON,
        "REFERENCES": REFERENCES,
    }

    if relationship_type not in relationship_map:
        return {
            "error": f"Unknown relationship type: {relationship_type}. Available: {list(relationship_map.keys())}"
        }

    try:
        with app_context.repo.transaction() as tx:
            # Use NeoAlchemy's built-in methods to find entities by primary key
            # Get the primary key field names
            from_primary_key = from_model_class.get_primary_key()
            to_primary_key = to_model_class.get_primary_key()

            if not from_primary_key:
                return {"error": f"No primary key defined for {from_entity_type}"}
            if not to_primary_key:
                return {"error": f"No primary key defined for {to_entity_type}"}

            # Find entities using kwargs with primary key field
            from_entity = tx.find_one(
                from_model_class, **{from_primary_key: from_entity_id}
            )
            if not from_entity:
                return {
                    "error": f"{from_entity_type} with {from_primary_key}='{from_entity_id}' not found"
                }

            to_entity = tx.find_one(to_model_class, **{to_primary_key: to_entity_id})
            if not to_entity:
                return {
                    "error": f"{to_entity_type} with {to_primary_key}='{to_entity_id}' not found"
                }

            # Create relationship using NeoAlchemy's validation
            relationship_properties = properties or {}
            relationship_class = relationship_map[relationship_type]
            rel = relationship_class.model_validate(relationship_properties)

            # Use NeoAlchemy's relate method which handles all the internals
            tx.relate(from_entity, rel, to_entity)

            return {
                "success": True,
                "message": f"Created {relationship_type} relationship",
                "from_entity": {"type": from_entity_type, "id": from_entity_id},
                "to_entity": {"type": to_entity_type, "id": to_entity_id},
                "relationship_type": relationship_type,
                "properties": relationship_properties,
            }

    except Exception as e:
        return {"error": f"Failed to create relationship: {str(e)}"}


async def _get_entity_relationships_impl(
    entity_type: str, entity_id: str, app_context, MODEL_MAP
) -> dict[str, Any]:
    """Get all relationships for an entity."""
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
            # Find the entity using NeoAlchemy's find_one method
            entity = tx.find_one(model_class, **{primary_key: entity_id})

            if not entity:
                return {
                    "error": f"{entity_type} with {primary_key}='{entity_id}' not found"
                }

            # This is a simplified implementation - in practice you'd query specific relationships
            return {
                "success": True,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "relationships": [],  # Would need more complex querying to populate
                "message": "Relationship querying not fully implemented",
            }

    except Exception as e:
        return {"error": f"Failed to get relationships for entity: {str(e)}"}


# =============================================================================
# MCP TOOL REGISTRATION
# =============================================================================


def register_relationship_tools(mcp: FastMCP, app_context, MODEL_MAP):
    """Register relationship management tools."""

    @mcp.tool()
    async def create_relationship(
        relationship_type: str,
        from_entity_type: str,
        from_entity_id: str,
        to_entity_type: str,
        to_entity_id: str,
        properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a relationship between two entities.

        Args:
            relationship_type: Type of relationship (e.g., 'CONTRIBUTES_TO', 'MANAGES', 'DEPENDS_ON', 'REFERS_TO')
            from_entity_type: Type of source entity
            from_entity_id: Primary key of source entity
            to_entity_type: Type of target entity
            to_entity_id: Primary key of target entity
            properties: Optional properties for the relationship

        Returns:
            Dictionary confirming the relationship creation with 'success' field
        """
        return await _create_relationship_impl(
            relationship_type,
            from_entity_type,
            from_entity_id,
            to_entity_type,
            to_entity_id,
            properties,
            app_context,
            MODEL_MAP,
        )

    @mcp.tool()
    async def get_entity_relationships(
        entity_type: str, entity_id: str
    ) -> dict[str, Any]:
        """Get all relationships for an entity.

        Args:
            entity_type: Type of entity
            entity_id: Primary key of the entity

        Returns:
            Dictionary containing list of relationships with 'success' field
        """
        return await _get_entity_relationships_impl(
            entity_type, entity_id, app_context, MODEL_MAP
        )
