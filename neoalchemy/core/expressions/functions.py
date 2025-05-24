"""
Function expressions for Neo4j Cypher queries.

This module provides expression classes that represent function calls
in Cypher queries, such as string functions, numeric functions, and
comparisons involving functions.
"""

from typing import Any, List

from neoalchemy.core.cypher.core.keywords import CypherKeywords as K
from neoalchemy.core.expressions.logical import LogicalExpr


class FunctionExpr(LogicalExpr):
    """A function expression (e.g., length(field)).

    Examples:
        Person.name.length()
        Person.email.lower()
    """

    def __init__(self, func_name: str, args: List[Any]):
        """Initialize a function expression.

        Args:
            func_name: Function name
            args: Function arguments
        """
        self.func_name = func_name
        self.args = args

    # to_cypher_element is now handled by the adapter in the base class

    def __eq__(self, value: Any) -> "FunctionComparisonExpr":  # type: ignore[override]
        """Compare function result with a value for equality.

        Args:
            value: Value to compare with

        Returns:
            A function comparison expression
        """
        return FunctionComparisonExpr(self, K.EQUALS, value)

    def __gt__(self, value: Any) -> "FunctionComparisonExpr":
        """Compare function result with a value (greater than).

        Args:
            value: Value to compare with

        Returns:
            A function comparison expression
        """
        return FunctionComparisonExpr(self, K.GT, value)

    def __lt__(self, value: Any) -> "FunctionComparisonExpr":
        """Compare function result with a value (less than).

        Args:
            value: Value to compare with

        Returns:
            A function comparison expression
        """
        return FunctionComparisonExpr(self, K.LT, value)

    def __ge__(self, value: Any) -> "FunctionComparisonExpr":
        """Compare function result with a value (greater than or equal).

        Args:
            value: Value to compare with

        Returns:
            A function comparison expression
        """
        return FunctionComparisonExpr(self, K.GTE, value)

    def __le__(self, value: Any) -> "FunctionComparisonExpr":
        """Compare function result with a value (less than or equal).

        Args:
            value: Value to compare with

        Returns:
            A function comparison expression
        """
        return FunctionComparisonExpr(self, K.LTE, value)

    def __ne__(self, value: Any) -> "FunctionComparisonExpr":  # type: ignore[override]
        """Compare function result with a value (not equal).

        Args:
            value: Value to compare with

        Returns:
            A function comparison expression
        """
        return FunctionComparisonExpr(self, K.NOT_EQUALS, value)


class FunctionComparisonExpr(LogicalExpr):
    """A comparison involving a function expression.

    Examples:
        Person.name.length() > 10
        Person.email.lower() == "alice@example.com"
    """

    def __init__(self, func_expr: FunctionExpr, operator: str, value: Any):
        """Initialize a function comparison expression.

        Args:
            func_expr: Function expression
            operator: Comparison operator
            value: Value to compare with
        """
        self.func_expr = func_expr
        self.operator = operator
        self.value = value

    # to_cypher_element is now handled by the adapter in the base class
