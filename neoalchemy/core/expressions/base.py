"""
Base expression classes for Neo4j Cypher queries.

This module provides the base classes for the expression system,
establishing the common interface and functionality for all expressions.
"""

from abc import ABC
from typing import TYPE_CHECKING, Any, ClassVar, Optional

from neoalchemy.core.cypher import CypherElement

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    pass


class Expr(ABC):
    """Base class for all expressions.

    All expression classes in the system derive from this base class,
    which defines the common interface for expressions.
    """

    # Class-level adapter for all expressions to use
    _adapter: ClassVar[Optional[Any]] = None

    @classmethod
    def get_adapter(cls) -> Any:
        """Get the current adapter instance.

        Creates a default adapter if none exists.

        Returns:
            The expression adapter
        """
        if cls._adapter is None:
            # Import here to avoid circular dependencies
            from neoalchemy.core.expressions.adapter import ExpressionAdapter

            cls._adapter = ExpressionAdapter()
        return cls._adapter

    @classmethod
    def set_adapter(cls, adapter: Any) -> None:
        """Set the adapter for all expressions.

        This allows configuration like changing the entity variable name.

        Args:
            adapter: The adapter instance to use
        """
        cls._adapter = adapter

    def to_cypher_element(self) -> CypherElement:
        """Convert the expression to a CypherElement.

        Uses the centralized adapter to convert expressions to cypher elements.

        Returns:
            A CypherElement representing this expression
        """
        return self.get_adapter().to_cypher_element(self)
