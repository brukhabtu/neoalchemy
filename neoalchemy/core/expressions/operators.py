"""
Operator expressions for Neo4j Cypher queries.

This module provides expression classes that represent operators in
Cypher queries, such as comparison operators, logical operators, and
composite expressions.
"""

from typing import Any

from neoalchemy.core.cypher import (
    ComparisonElement,
    CypherElement,
    LogicalElement,
    NegationElement,
    PropertyRef,
)
from neoalchemy.core.expressions.logical import LogicalExpr


class OperatorExpr(LogicalExpr):
    """An expression with an operator (e.g., field = value).

    Examples:
        Person.age > 30
        Person.name == "Alice"
        Person.active != True
    """

    def __init__(self, field: str, operator: str, value: Any):
        """Initialize an operator expression.

        Args:
            field: Field name
            operator: Operator string (=, >, <, etc.)
            value: Value to compare with
        """
        self.field = field
        self.operator = operator
        self.value = value

    # to_cypher_element is now handled by the adapter in the base class


class CompositeExpr(LogicalExpr):
    """A composite expression combining two expressions with a logical operator.

    Examples:
        Person.age > 30 and Person.name == "Alice"
        Person.active == True or Person.role == "admin"
    """

    def __init__(self, left: LogicalExpr, op: str, right: LogicalExpr):
        """Initialize a composite expression.

        Args:
            left: Left expression
            op: Operator (AND, OR)
            right: Right expression
        """
        self.left = left
        self.op = op
        self.right = right

    # to_cypher_element is now handled by the adapter in the base class


class NotExpr(LogicalExpr):
    """A negated expression.

    Examples:
        not (Person.age > 30)
        not (Person.name.startswith("A"))
    """

    def __init__(self, expr: LogicalExpr):
        """Initialize a NOT expression.

        Args:
            expr: Expression to negate
        """
        self.expr = expr

    # to_cypher_element is now handled by the adapter in the base class
