"""
Logical expression classes for Neo4j Cypher queries.

This module provides expression classes that represent logical operations
in Cypher queries, such as AND, OR, and NOT operations between expressions.
"""

from neoalchemy.core.cypher.core.keywords import CypherKeywords as K
from neoalchemy.core.expressions.base import Expr


class LogicalExpr(Expr):
    """Base class for expressions that support logical operations.

    Provides logical operator methods using Python's bitwise operators:
    - & for logical AND
    - | for logical OR
    - ~ for logical NOT

    Note: NeoAlchemy uses bitwise operators (&, |, ~) rather than Python's
    logical operators (and, or, not) due to Python's short-circuit evaluation
    which prevents proper expression composition.

    Examples:
        # Correct usage with bitwise operators
        (Person.age > 30) & (Person.active == True)      # AND
        (Person.role == "admin") | (Person.role == "manager")  # OR
        ~(Person.active == True)                         # NOT

        # This won't work as expected (uses Python's logical operators)
        (Person.age > 30) and (Person.active == True)   # Don't use
        (Person.role == "admin") or (Person.role == "manager")  # Don't use
        not (Person.active == True)                      # Don't use
    """

    def __and__(self, other: "LogicalExpr") -> "LogicalExpr":
        """Combine with another expression using logical AND.

        This supports the bitwise & operator:
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

        This supports the bitwise | operator:
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

        This supports the bitwise ~ operator:
        ~expr

        Returns:
            A new expression representing the logical NOT
        """
        from neoalchemy.core.expressions.operators import NotExpr

        return NotExpr(self)
