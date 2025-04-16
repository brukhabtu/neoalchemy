"""
Core components for the NeoAlchemy ORM.

This package contains the core components of the NeoAlchemy ORM system,
including expressions, field registration, and state management.
"""

# Import important components for public API
from neoalchemy.core.expressions import (
    Expr, FieldExpr, OperatorExpr, CompositeExpr, 
    NotExpr, FunctionExpr, FunctionComparisonExpr
)
from neoalchemy.core.field_registration import (
    initialize, register_array_field, get_array_fields, add_field_expressions
)
from neoalchemy.core.state import expression_state
from neoalchemy.core.cypher import (
    CypherElement, CypherClause, CypherQuery,
    NodePattern, RelationshipPattern, PathPattern, PropertyRef,
    MatchClause, WhereClause, ReturnClause, OrderByClause,
    LimitClause, SkipClause, WithClause
)

# Define what's exported when someone does "from neoalchemy.core import *"
__all__ = [
    # Expressions
    'Expr', 'FieldExpr', 'OperatorExpr', 'CompositeExpr', 
    'NotExpr', 'FunctionExpr', 'FunctionComparisonExpr',
    
    # Field registration
    'initialize', 'register_array_field', 'get_array_fields', 'add_field_expressions',
    
    # State management
    'expression_state',
    
    # Cypher
    'CypherElement', 'CypherClause', 'CypherQuery',
    'NodePattern', 'RelationshipPattern', 'PathPattern', 'PropertyRef',
    'MatchClause', 'WhereClause', 'ReturnClause', 'OrderByClause',
    'LimitClause', 'SkipClause', 'WithClause'
]