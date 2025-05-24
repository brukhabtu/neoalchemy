"""
Expression system for building Neo4j Cypher queries in a Pythonic way.

This package provides a set of classes that allow building Neo4j Cypher
queries using Python's natural syntax, including comparisons, logical
operations, and string/array operations.
"""

from neoalchemy.core.expressions.adapter import ExpressionAdapter
from neoalchemy.core.expressions.base import Expr
from neoalchemy.core.expressions.fields import FieldExpr
from neoalchemy.core.expressions.functions import FunctionComparisonExpr, FunctionExpr
from neoalchemy.core.expressions.logical import LogicalExpr
from neoalchemy.core.expressions.operators import CompositeExpr, NotExpr, OperatorExpr

__all__ = [
    "Expr",
    "LogicalExpr",
    "FieldExpr",
    "OperatorExpr",
    "CompositeExpr",
    "NotExpr",
    "FunctionExpr",
    "FunctionComparisonExpr",
    "ExpressionAdapter",
]
