"""
Core components for the NeoAlchemy ORM.

This package contains the core components of the NeoAlchemy ORM system,
including expressions, field registration, and state management.
"""

# Import important components for public API
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
    get_array_fields,
    initialize,
    register_array_field,
)
from neoalchemy.core.state import expression_state

# Define what's exported when someone does "from neoalchemy.core import *"
__all__ = [
    # Expressions
    "Expr",
    "FieldExpr",
    "OperatorExpr",
    "CompositeExpr",
    "NotExpr",
    "FunctionExpr",
    "FunctionComparisonExpr",
    # Field registration
    "initialize",
    "register_array_field",
    "get_array_fields",
    "add_field_expressions",
    # State management
    "expression_state",
    # Cypher
    "CypherElement",
    "CypherClause",
    "CypherQuery",
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
]
