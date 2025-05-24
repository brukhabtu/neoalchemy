"""
Logical expression classes for Neo4j Cypher queries.

This module provides expression classes that represent logical operations
in Cypher queries, such as AND, OR, and NOT operations between expressions.
"""

from neoalchemy.core.cypher.core.keywords import CypherKeywords as K
from neoalchemy.core.expressions.base import Expr


class LogicalExpr(Expr):
    """Base class for expressions that support logical operations.

    Provides logical operator methods like __and__, __or__, and __invert__
    that can be used to combine expressions with AND, OR, and NOT logic.
    """

    def __and__(self, other: "LogicalExpr") -> "LogicalExpr":
        """Combine with another expression using logical AND.

        This supports the Python 'and' operator:
        expr1 & expr2

        Args:
            other: Another expression

        Returns:
            A new expression representing the logical AND
        """
        from neoalchemy.core.expressions.operators import CompositeExpr

        return CompositeExpr(self, K.AND, other)

    def __or__(self, other: "LogicalExpr") -> "LogicalExpr":
        """Combine with another expression using logical OR.

        This supports the Python 'or' operator:
        expr1 | expr2

        Args:
            other: Another expression

        Returns:
            A new expression representing the logical OR
        """
        from neoalchemy.core.expressions.operators import CompositeExpr

        return CompositeExpr(self, K.OR, other)

    def __invert__(self) -> "LogicalExpr":
        """Negate this expression (logical NOT).

        This supports the Python unary negation:
        ~expr

        Returns:
            A new expression representing the logical NOT
        """
        from neoalchemy.core.expressions.operators import NotExpr

        return NotExpr(self)
