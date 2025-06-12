"""
NeoAlchemy: A SQLAlchemy-inspired ORM for Neo4j.

This package provides a high-level, intuitive API for working with Neo4j
graph databases using Pydantic models with a transaction-based interface.
"""

# Re-export from modules
from neoalchemy.constraints import setup_constraints
from neoalchemy.core.cypher import (
    CypherClause,
    CypherElement,
    CypherQuery,
    LimitClause,
    MatchClause,
    NodePattern,
    OrderByClause,
    PathPattern,
    PropertyRef,
    RelationshipPattern,
    ReturnClause,
    SkipClause,
    WhereClause,
    WithClause,
)
from neoalchemy.core.expressions import (
    CompositeExpr,
    Expr,
    FieldExpr,
    FunctionComparisonExpr,
    FunctionExpr,
    NotExpr,
    OperatorExpr,
)
from neoalchemy.core.field_registration import (
    add_field_expressions,
    initialize,
    register_array_field,
)
from neoalchemy.orm.fields import IndexedField, PrimaryField, UniqueField
from neoalchemy.orm.models import Neo4jModel, Node, Relationship
from neoalchemy.orm.query import QueryBuilder
from neoalchemy.orm.repository import Neo4jRepository, Neo4jTransaction
from neoalchemy.orm.tracking import SOURCED_FROM, Source, SourceScheme

# No automatic initialization - users need to call initialize() explicitly

__version__ = "0.1.0"

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
    # Custom field types
    "UniqueField",
    "IndexedField",
    "PrimaryField",
    # Cypher
    "CypherQuery",
    "CypherElement",
    "CypherClause",
    "NodePattern",
    "RelationshipPattern",
    "PathPattern",
    "PropertyRef",
    "MatchClause",
    "WhereClause",
    "ReturnClause",
    "OrderByClause",
    "LimitClause",
    "SkipClause",
    "WithClause",
    # Repository
    "Neo4jRepository",
    "Neo4jTransaction",
    # Query building
    "QueryBuilder",
    # Constraints
    "setup_constraints",
    # Source tracking
    "SourceScheme",
    "Source",
    "SOURCED_FROM",
    # Utility functions
    "add_field_expressions",
    "initialize",
    "register_array_field",
]
