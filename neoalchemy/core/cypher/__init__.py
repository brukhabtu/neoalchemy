"""
Cypher compiler system for Neo4j queries.

This package provides a set of classes for building and compiling
Cypher queries in a composable, object-oriented way.
"""

# Import from elements
from neoalchemy.core.cypher.elements.element import CypherElement
from neoalchemy.core.cypher.core.keywords import (
    CypherKeywords, ClauseKeyword, OperatorKeyword,
    LogicalKeyword, DirectionKeyword, FunctionKeyword
)

# Import from elements
from neoalchemy.core.cypher.elements.basic import (
    PropertyRef, ComparisonElement, LogicalElement,
    NegationElement, FunctionCallElement
)
from neoalchemy.core.cypher.elements.patterns import (
    NodePattern, RelationshipPattern, PathPattern
)
from neoalchemy.core.cypher.elements.clauses import (
    CypherClause, MatchClause, WhereClause, ReturnClause,
    OrderByClause, LimitClause, SkipClause, WithClause
)

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
    "FunctionKeyword"
]