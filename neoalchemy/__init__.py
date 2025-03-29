"""
NeoAlchemy: A SQLAlchemy-inspired ORM for Neo4j.

This package provides a high-level, intuitive API for working with Neo4j
graph databases using Pydantic models with a transaction-based interface.
"""

# Re-export from modules
from neoalchemy.expressions import (
    Expr, FieldExpr, OperatorExpr, CompositeExpr, 
    NotExpr, FunctionExpr, FunctionComparisonExpr
)

from neoalchemy.field_registration import (
    add_field_expressions, initialize, register_array_field
)

from neoalchemy.models import (
    Neo4jModel, Node, Relationship
)

from neoalchemy.repository import Neo4jRepository, Neo4jTransaction

# No automatic initialization - users need to call initialize() explicitly

__all__ = [
    # Base models
    "Neo4jModel",
    "Node",
    "Relationship",
    # Field expressions
    "Expr",
    "FieldExpr",
    "OperatorExpr",
    "CompositeExpr",
    "NotExpr",
    "FunctionExpr", 
    "FunctionComparisonExpr",
    # Repository
    "Neo4jRepository",
    "Neo4jTransaction",
    # Utility functions
    "add_field_expressions",
    "initialize",
    "register_array_field",
]