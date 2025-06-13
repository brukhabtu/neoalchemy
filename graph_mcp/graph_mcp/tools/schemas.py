"""
Schema resources for API discovery.

This module contains MCP resources that provide static schema information
about entity types and relationship types. These resources use REST-style 
URIs and are accessible without function calls.
"""

from typing import Any

from fastmcp import FastMCP

from graph_mcp.models import TaskStatus

# =============================================================================
# BUSINESS LOGIC FUNCTIONS
# =============================================================================


async def _get_enum_types_impl() -> dict[str, Any]:
    """Business logic for getting available enum types."""
    enum_types = {
        "TaskStatus": [ts.value for ts in TaskStatus],
    }

    return {
        "enum_types": enum_types,
        "description": "Valid enum values for entity properties",
    }


async def _get_entity_types_impl(NODE_MODELS) -> dict[str, Any]:
    """Business logic for getting available entity types with schemas."""
    entity_types = []
    for name, model_class in NODE_MODELS.items():
        try:
            schema = model_class.model_json_schema()
            entity_types.append(
                {
                    "name": name,
                    "type": "Node",
                    "schema": schema,
                    "docstring": model_class.__doc__,
                    "example": _generate_example_from_schema(schema),
                }
            )
        except Exception as e:
            entity_types.append(
                {
                    "name": name,
                    "type": "Node",
                    "error": f"Could not generate schema: {str(e)}",
                }
            )

    return {"entities": entity_types, "count": len(entity_types)}


async def _get_relationship_types_impl(RELATIONSHIP_MODELS) -> dict[str, Any]:
    """Business logic for getting available relationship types with schemas."""
    relationship_types = []
    for name, model_class in RELATIONSHIP_MODELS.items():
        try:
            schema = model_class.model_json_schema()
            relationship_types.append(
                {
                    "name": name,
                    "type": "Relationship",
                    "schema": schema,
                    "docstring": model_class.__doc__,
                    "example": _generate_example_from_schema(schema),
                }
            )
        except Exception as e:
            relationship_types.append(
                {
                    "name": name,
                    "type": "Relationship",
                    "error": f"Could not generate schema: {str(e)}",
                }
            )

    return {"relationships": relationship_types, "count": len(relationship_types)}


async def _get_entity_schema_impl(entity_type: str, NODE_MODELS) -> dict[str, Any]:
    """Business logic for getting detailed schema for a specific entity type."""
    if entity_type not in NODE_MODELS:
        available_types = list(NODE_MODELS.keys())
        return {
            "error": f"Unknown entity type: {entity_type}. Available entities: {available_types}"
        }

    model_class = NODE_MODELS[entity_type]

    try:
        schema = model_class.model_json_schema()

        return {
            "entity_type": entity_type,
            "type": "Node",
            "schema": schema,
            "docstring": model_class.__doc__,
            "example": _generate_example_from_schema(schema),
            "required_fields": schema.get("required", []),
            "properties": schema.get("properties", {}),
        }

    except Exception as e:
        return {
            "error": f"Failed to generate schema for entity {entity_type}: {str(e)}"
        }


async def _get_relationship_schema_impl(
    relationship_type: str, RELATIONSHIP_MODELS
) -> dict[str, Any]:
    """Business logic for getting detailed schema for a specific relationship type."""
    if relationship_type not in RELATIONSHIP_MODELS:
        available_types = list(RELATIONSHIP_MODELS.keys())
        return {
            "error": (
                f"Unknown relationship type: {relationship_type}. "
                f"Available relationships: {available_types}"
            )
        }

    model_class = RELATIONSHIP_MODELS[relationship_type]

    try:
        schema = model_class.model_json_schema()

        return {
            "relationship_type": relationship_type,
            "type": "Relationship",
            "schema": schema,
            "docstring": model_class.__doc__,
            "example": _generate_example_from_schema(schema),
            "required_fields": schema.get("required", []),
            "properties": schema.get("properties", {}),
        }

    except Exception as e:
        return {
            "error": f"Failed to generate schema for relationship {relationship_type}: {str(e)}"
        }


# =============================================================================
# MCP RESOURCE REGISTRATION
# =============================================================================


def register_schema_resources(mcp: FastMCP):
    """Register all schema-related MCP resources."""

    # Access the model registries from the base classes
    from neoalchemy.orm.models import Node, Relationship

    NODE_MODELS = Node.__registry__
    RELATIONSHIP_MODELS = Relationship.__registry__

    @mcp.resource("schema://enums/")
    async def get_enum_types():
        """List all available enum types for entity properties."""
        return await _get_enum_types_impl()

    @mcp.resource("schema://entities/")
    async def get_entity_types():
        """List all available entity types with their schemas."""
        return await _get_entity_types_impl(NODE_MODELS)

    @mcp.resource("schema://relationships/")
    async def get_relationship_types():
        """List all available relationship types with their schemas."""
        return await _get_relationship_types_impl(RELATIONSHIP_MODELS)

    @mcp.resource("schema://entities/{entity_type}")
    async def get_entity_schema(entity_type: str):
        """Get detailed JSON schema for a specific entity type."""
        return await _get_entity_schema_impl(entity_type, NODE_MODELS)

    @mcp.resource("schema://relationships/{relationship_type}")
    async def get_relationship_schema(relationship_type: str):
        """Get detailed JSON schema for a specific relationship type."""
        return await _get_relationship_schema_impl(
            relationship_type, RELATIONSHIP_MODELS
        )


def _generate_example_from_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Generate an example instance from a JSON schema.

    Args:
        schema: JSON schema dictionary

    Returns:
        Example instance dictionary
    """
    example = {}
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    for field_name, field_info in properties.items():
        field_type = field_info.get("type", "string")

        # Generate appropriate example values based on type
        if field_name in required or field_info.get("default") is None:
            if field_type == "string":
                if "email" in field_name.lower():
                    example[field_name] = "example@company.com"
                elif "name" in field_name.lower():
                    example[field_name] = "Example Name"
                elif "id" in field_name.lower():
                    example[field_name] = "example-id-123"
                else:
                    example[field_name] = f"example_{field_name}"
            elif field_type == "integer":
                example[field_name] = 1
            elif field_type == "number":
                example[field_name] = 1.0
            elif field_type == "boolean":
                example[field_name] = True
            elif field_type == "array":
                example[field_name] = ["example_item"]
            elif field_type == "object":
                example[field_name] = {"key": "value"}

        # Use default value if available
        elif "default" in field_info:
            example[field_name] = field_info["default"]

    return example
