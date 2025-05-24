"""
Cypher compiler system for Neo4j queries.

This package provides a set of classes for building and compiling
Cypher queries in a composable, object-oriented way.
"""

# Import from elements
from neoalchemy.core.cypher.core.keywords import (
    ClauseKeyword,
    CypherKeywords,
    DirectionKeyword,
    FunctionKeyword,
    LogicalKeyword,
    OperatorKeyword,
)

# Import from elements
from neoalchemy.core.cypher.elements.basic import (
    ComparisonElement,
    FunctionCallElement,
    LogicalElement,
    NegationElement,
    PropertyRef,
)
from neoalchemy.core.cypher.elements.clauses import (
    CypherClause,
    LimitClause,
    MatchClause,
    OrderByClause,
    ReturnClause,
    SkipClause,
    WhereClause,
    WithClause,
)
from neoalchemy.core.cypher.elements.element import CypherElement
from neoalchemy.core.cypher.elements.patterns import NodePattern, PathPattern, RelationshipPattern

# Import from query
from neoalchemy.core.cypher.query import CypherQuery

# Define what's exported when someone does "from neoalchemy.core.cypher import *"
__all__ = [
    # Base elements
    "CypherElement",
    "PropertyRef",
    "ComparisonElement",
    "LogicalElement",
    "NegationElement",
    "FunctionCallElement",
    # Patterns
    "NodePattern",
    "RelationshipPattern",
    "PathPattern",
    # Clauses
    "CypherClause",
    "MatchClause",
    "WhereClause",
    "ReturnClause",
    "OrderByClause",
    "LimitClause",
    "SkipClause",
    "WithClause",
    # Query
    "CypherQuery",
    # Keywords
    "CypherKeywords",
    "ClauseKeyword",
    "OperatorKeyword",
    "LogicalKeyword",
    "DirectionKeyword",
    "FunctionKeyword",
]
