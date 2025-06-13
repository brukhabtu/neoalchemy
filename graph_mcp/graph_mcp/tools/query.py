"""
Generic query tools for NeoAlchemy models.

Allows LLMs to construct NeoAlchemy query expressions directly using a safe
evaluation environment with restricted namespaces.
"""

import ast
from typing import Any

from fastmcp import FastMCP

# =============================================================================
# SAFE QUERY EVALUATION
# =============================================================================


def _create_safe_namespace(model_class):
    """Create a safe namespace for evaluating query expressions."""
    # Model fields - dynamically add all field names from the model
    model_fields = {}
    for field_name in model_class.model_fields:
        if hasattr(model_class, field_name):
            model_fields[field_name] = getattr(model_class, field_name)

    # Combine safe namespace
    safe_namespace = {
        "__builtins__": {},  # Remove all builtins for safety
        **model_fields,
        # Common values
        "True": True,
        "False": False,
        "None": None,
    }

    return safe_namespace


def _is_safe_expression(expr_str: str) -> bool:
    """Check if the expression string is safe to evaluate."""
    try:
        # Parse the expression into an AST
        tree = ast.parse(expr_str, mode="eval")

        # Define allowed node types for safety
        allowed_nodes = {
            ast.Expression,
            ast.Name,
            ast.Load,
            ast.Constant,
            ast.BinOp,
            ast.Compare,
            ast.BoolOp,
            ast.UnaryOp,
            ast.Attribute,
            ast.Call,
            ast.And,
            ast.Or,
            ast.Not,
            ast.Eq,
            ast.NotEq,
            ast.Lt,
            ast.LtE,
            ast.Gt,
            ast.GtE,
            ast.In,
            ast.NotIn,
            ast.Is,
            ast.IsNot,
        }

        # Check all nodes in the AST
        for node in ast.walk(tree):
            if type(node) not in allowed_nodes:
                return False

            # Additional safety checks
            if isinstance(node, ast.Call):
                # Only allow calls to simple names (no complex expressions)
                if not isinstance(node.func, (ast.Name, ast.Attribute)):
                    return False

            if isinstance(node, ast.Name):
                # Prevent access to dangerous names
                dangerous_names = {
                    "eval",
                    "exec",
                    "compile",
                    "__import__",
                    "open",
                    "file",
                }
                if node.id in dangerous_names:
                    return False

        return True
    except:
        return False


async def _query_with_expression_impl(
    entity_type: str,
    where_expression: str | None,
    limit: int,
    app_context,
    MODEL_MAP,
) -> dict[str, Any]:
    """Query entities using NeoAlchemy ORM with safe expression evaluation."""
    if entity_type not in MODEL_MAP:
        available_types = list(MODEL_MAP.keys())
        return {
            "error": f"Unknown entity type: {entity_type}. Available types: {available_types}"
        }

    model_class = MODEL_MAP[entity_type]

    try:
        with app_context.repo.transaction() as tx:
            # Start with base query
            query = tx.query(model_class)

            # Apply where expression if provided
            if where_expression:
                # Safety check
                if not _is_safe_expression(where_expression):
                    return {
                        "error": "Unsafe expression detected. Only field comparisons and logical operators are allowed."
                    }

                # Create safe namespace with model fields
                safe_namespace = _create_safe_namespace(model_class)

                try:
                    # Safely evaluate the expression
                    condition = eval(where_expression, safe_namespace)
                    query = query.where(condition)
                except Exception as e:
                    return {"error": f"Invalid expression: {str(e)}"}

            # Execute query with limit
            if limit > 0:
                query = query.limit(limit)

            entities = query.find()

            # Convert to dict format with primary key identification
            results = []
            for entity in entities:
                entity_dict = entity.model_dump()

                # Add primary key for easy reference
                try:
                    primary_key = entity.get_primary_key()
                    if primary_key:
                        entity_dict["_primary_key"] = primary_key
                except:
                    # Fallback if get_primary_key() doesn't exist
                    pass

                results.append(entity_dict)

            return {
                "success": True,
                "entity_type": entity_type,
                "where_expression": where_expression,
                "count": len(results),
                "entities": results,
                "limited": limit > 0 and len(results) == limit,
            }

    except Exception as e:
        return {"error": f"Query failed: {str(e)}"}


async def _query_relationships_impl(
    relationship_type: str,
    where_expression: str | None,
    limit: int,
    app_context,
    MODEL_MAP,
) -> dict[str, Any]:
    """Query relationships using NeoAlchemy ORM with safe expression evaluation."""
    if relationship_type not in MODEL_MAP:
        available_types = list(MODEL_MAP.keys())
        return {
            "error": f"Unknown relationship type: {relationship_type}. Available types: {available_types}"
        }

    relationship_class = MODEL_MAP[relationship_type]

    try:
        with app_context.repo.transaction() as tx:
            # Start with base relationship query
            query = tx.query(relationship_class)

            # Apply where expression if provided
            if where_expression:
                # Safety check
                if not _is_safe_expression(where_expression):
                    return {
                        "error": "Unsafe expression detected. Only field comparisons and logical operators are allowed."
                    }

                # Create safe namespace with relationship fields
                safe_namespace = _create_safe_namespace(relationship_class)

                try:
                    # Safely evaluate the expression
                    condition = eval(where_expression, safe_namespace)
                    query = query.where(condition)
                except Exception as e:
                    return {"error": f"Invalid expression: {str(e)}"}

            # Execute query with limit
            if limit > 0:
                query = query.limit(limit)

            relationships = query.find()

            # Convert to dict format
            results = []
            for rel in relationships:
                rel_dict = rel.model_dump()
                results.append(rel_dict)

            return {
                "success": True,
                "relationship_type": relationship_type,
                "where_expression": where_expression,
                "count": len(results),
                "relationships": results,
                "limited": limit > 0 and len(results) == limit,
            }

    except Exception as e:
        return {"error": f"Relationship query failed: {str(e)}"}


async def _cypher_query_impl(
    cypher: str,
    parameters: dict[str, Any] | None,
    limit: int,
    read_only: bool,
    app_context,
) -> dict[str, Any]:
    """Execute a raw Cypher query."""
    try:
        # Safety checks for read-only mode
        if read_only:
            cypher_upper = cypher.upper().strip()
            write_keywords = ["CREATE", "MERGE", "SET", "DELETE", "REMOVE", "DROP"]

            for keyword in write_keywords:
                if keyword in cypher_upper:
                    return {
                        "error": f"Write operation '{keyword}' not allowed in read-only mode"
                    }

        # Add LIMIT if not present and limit is specified
        cypher_upper = cypher.upper()
        if limit > 0 and "LIMIT" not in cypher_upper:
            cypher = f"{cypher} LIMIT {limit}"

        with app_context.repo.transaction() as tx:
            result = tx.run(cypher, parameters or {})

            # Convert results to list of dictionaries
            records = []
            for record in result:
                record_dict = dict(record)
                records.append(record_dict)

            return {
                "success": True,
                "cypher": cypher,
                "parameters": parameters or {},
                "read_only": read_only,
                "count": len(records),
                "records": records,
                "limited": limit > 0 and len(records) == limit,
            }

    except Exception as e:
        return {"error": f"Cypher query failed: {str(e)}"}


# =============================================================================
# MCP TOOL REGISTRATION
# =============================================================================


def register_query_tools(mcp: FastMCP, app_context, MODEL_MAP):
    """Register NeoAlchemy expression-based query tools."""

    @mcp.tool()
    async def query_entities(
        entity_type: str, where: str | None = None, limit: int = 50
    ) -> dict[str, Any]:
        """Query entities using NeoAlchemy ORM with expression-based filtering.

        Args:
            entity_type: Type of entity to query (e.g., 'Person', 'Account', 'Team', 'Project', 'Source')
            where: Optional where expression using NeoAlchemy syntax. Examples:
                  - "name == 'John'"
                  - "is_active == True"
                  - "age > 25"
                  - "name.contains('john')"
                  - "created_at > '2024-01-01'"
                  - "(age > 25) & (is_active == True)"
                  - "name.startswith('J') | name.endswith('n')"
            limit: Maximum number of results to return (default: 50, 0 for no limit)

        Returns:
            Dictionary containing matching entities with type validation and primary keys

        Note: Only field comparisons and logical operators are allowed for security.
        Available field methods: contains(), startswith(), endswith(), is_null(), is_not_null()
        """
        return await _query_with_expression_impl(
            entity_type, where, limit, app_context, MODEL_MAP
        )

    @mcp.tool()
    async def query_relationships(
        relationship_type: str, where: str | None = None, limit: int = 50
    ) -> dict[str, Any]:
        """Query relationships using NeoAlchemy ORM with expression-based filtering.

        Args:
            relationship_type: Type of relationship to query (e.g., 'HAS_ACCOUNT', 'BELONGS_TO', 'WORKS_ON', 'SOURCED_FROM')
            where: Optional where expression using NeoAlchemy syntax (same format as query_entities)
            limit: Maximum number of results to return (default: 50, 0 for no limit)

        Returns:
            Dictionary containing matching relationships with type validation
        """
        return await _query_relationships_impl(
            relationship_type, where, limit, app_context, MODEL_MAP
        )

    @mcp.tool()
    async def cypher_query(
        cypher: str,
        parameters: dict[str, Any] | None = None,
        limit: int = 100,
        read_only: bool = True,
    ) -> dict[str, Any]:
        """Execute a raw Cypher query.

        Args:
            cypher: Cypher query string
            parameters: Optional parameters for the query
            limit: Maximum number of results to return (default: 100, 0 for no limit)
            read_only: If true, prevents write operations for safety (default: true)

        Returns:
            Dictionary containing query results

        Note: When read_only=true, write operations (CREATE, MERGE, SET, DELETE, etc.) are blocked.
        """
        return await _cypher_query_impl(
            cypher, parameters, limit, read_only, app_context
        )
