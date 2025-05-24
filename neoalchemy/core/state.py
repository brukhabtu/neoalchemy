"""
State management for expressions and transactions.

This module provides utilities for maintaining state across expression evaluations,
especially for Pythonic operations like chained comparisons and containment checks.
"""

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")

from neoalchemy.core.expressions.base import Expr


@dataclass
class ExpressionState:
    """Holds state for expression evaluation.

    This class keeps track of expressions created during operations like
    containment checks (x in y) and chained comparisons (x < y < z).
    """

    last_expr: Optional[Expr] = None  # For "in" operator support
    chain_expr: Optional[Expr] = None  # For chained comparisons
    is_capturing: bool = False  # Whether to capture expressions


# Global expression state instance
expression_state = ExpressionState()


@contextmanager
def expression_capture():
    """Context manager for capturing expressions during evaluation.

    This allows the query builder to capture expressions created during
    Pythonic operations like 'in' operators or chained comparisons.

    Example:
        with expression_capture():
            "John" in Person.name  # This will set expression_state.last_expr
    """
    # Set capturing state to True at entry
    old_value = expression_state.is_capturing
    expression_state.is_capturing = True

    try:
        yield
    finally:
        # Restore previous capturing state
        expression_state.is_capturing = old_value


def reset_expression_state():
    """Reset all expression state variables.

    This ensures that no lingering state affects future expressions.
    """
    expression_state.last_expr = None
    expression_state.chain_expr = None


def capture_expression(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for methods that should capture expressions.

    This decorator automatically captures expressions created by methods
    like __contains__, making them available to the query builder.

    Args:
        func: The function to decorate

    Returns:
        Decorated function
    """

    def wrapper(*args: Any, **kwargs: Any) -> T:
        # Call the original function
        result = func(*args, **kwargs)

        # We keep the expression in the global state regardless of capturing context
        # The expression will be picked up by the query builder's where() method

        return result

    return wrapper
