"""
Field expressions for Neo4j Cypher queries.

This module provides field expression classes that represent fields (properties)
in Neo4j nodes and relationships. These expressions form the foundation of the
Pythonic query API.
"""

from typing import Any, List, Optional

from neoalchemy.core.expressions.logical import LogicalExpr
from neoalchemy.core.state import expression_state


class FieldExpr(LogicalExpr):
    """Represents a field (property) in a Neo4j node or relationship.

    This class forms the foundation of the expression system, allowing fields
    to be used in comparison operations and function calls.

    Examples:
        Person.name          # A field expression for the 'name' property
        Person.age > 30      # Creates an OperatorExpr
        "Smith" in Person.last_name  # Creates a containment OperatorExpr
    """

    def __init__(self, name: str, array_field_types: Optional[List[str]] = None):
        """Initialize a field expression.

        Args:
            name: Field name in the database
            array_field_types: Optional list of field types known to be arrays
        """
        self.name = name
        self._array_field_types = array_field_types or []

    def is_array_field(self) -> bool:
        """Determine if this field likely represents an array/list.

        Uses naming conventions and known array field types to determine
        if a field is an array/collection.

        Returns:
            True if the field is likely an array, False otherwise
        """
        # Fields that are known to be arrays
        array_field_names = [
            "participants",
            "keywords",
            "tags",
            "sources",
        ] + self._array_field_types

        # Check for exact matches in known array fields
        if self.name in array_field_names:
            return True

        # Check for plurals (fields ending with 's')
        # This is a heuristic and might not be 100% accurate
        if self.name.endswith("s") and not self.name.endswith("ss"):  # Avoid things like 'address'
            return True

        return False

    # to_cypher_element is now handled by the adapter in the base class

    def __contains__(self, value: Any) -> bool:
        """Create a 'contains' expression for string or array containment checks.

        This method enables the Pythonic 'in' operator syntax for queries:
        "Smith" in Person.last_name

        Must be used inside a transaction context.

        Args:
            value: The value to check for containment

        Returns:
            Always returns True, but records the expression in the current transaction
        """
        from neoalchemy.core.cypher.core.keywords import CypherKeywords as K
        from neoalchemy.core.expressions.operators import OperatorExpr
        from neoalchemy.core.state import expression_state

        # Create the appropriate expression based on field type
        if self.is_array_field():
            # For arrays/lists, use ANY IN operator in Neo4j
            expr = OperatorExpr(self.name, K.ANY_IN, value)
        else:
            # For strings, use CONTAINS operator
            expr = OperatorExpr(self.name, K.CONTAINS, value)

        # Record the expression for later use by the query builder
        # Even if we're not in a capturing context, it's harmless to set this
        expression_state.last_expr = expr

        # Always return True - this is required by the Python language
        # The query builder will retrieve the expression from expression_state later
        return True

    def contains(self, value: Any) -> LogicalExpr:
        """Check if field contains a value (string or collection).

        This is an explicit method alternative to the `in` operator.
        For string fields, checks substring containment.
        For array fields, checks if the array contains the value.

        Examples:
            Person.last_name.contains("Smith")  # String containment
            Event.participants.contains("Alice")  # Array containment

        Args:
            value: Value to check for containment

        Returns:
            An expression for containment check
        """
        from neoalchemy.core.cypher.core.keywords import CypherKeywords as K
        from neoalchemy.core.expressions.operators import OperatorExpr

        if self.is_array_field():
            # For arrays, check array membership
            return OperatorExpr(self.name, K.ANY_IN, value)
        else:
            # For strings, check substring containment
            return OperatorExpr(self.name, K.CONTAINS, value)

    def __eq__(self, value: Any) -> LogicalExpr:  # type: ignore[override]
        """Create an equality expression.

        Supports both direct comparisons and chained comparisons.

        Args:
            value: The value to compare with

        Returns:
            An expression for equality comparison
        """
        from neoalchemy.core.cypher.core.keywords import CypherKeywords as K
        from neoalchemy.core.expressions.operators import OperatorExpr

        if value is None:
            return self.is_null()

        # Create the expression
        expr = OperatorExpr(self.name, K.EQUALS, value)

        # Check if we're in the middle of a chained comparison
        if expression_state.chain_expr is not None:
            # Get the first part of the chain
            left_expr = expression_state.chain_expr
            # Clear the chain state
            expression_state.chain_expr = None
            # Combine with AND
            return left_expr.__and__(expr)

        # Only store for chaining if we're in a transaction context
        if expression_state.is_capturing:
            # Store this expression for potential chaining
            expression_state.chain_expr = expr

        return expr

    def __gt__(self, value: Any) -> LogicalExpr:
        """Create a greater than expression.

        Supports both direct comparisons and chained comparisons.

        Args:
            value: The value to compare with

        Returns:
            An expression for greater than comparison
        """
        from neoalchemy.core.expressions.operators import OperatorExpr

        # Create the expression
        expr = OperatorExpr(self.name, ">", value)

        # Check if we're in the middle of a chained comparison
        if expression_state.chain_expr is not None:
            # Get the first part of the chain
            left_expr = expression_state.chain_expr
            # Clear the chain state
            expression_state.chain_expr = None
            # Combine with AND
            return left_expr.__and__(expr)

        # Only store for chaining if we're in a transaction context
        if expression_state.is_capturing:
            # Store this expression for potential chaining
            expression_state.chain_expr = expr

        return expr

    def __lt__(self, value: Any) -> LogicalExpr:
        """Create a less than expression.

        Supports both direct comparisons and chained comparisons.

        Args:
            value: The value to compare with

        Returns:
            An expression for less than comparison
        """
        from neoalchemy.core.expressions.operators import OperatorExpr

        # Create the expression
        expr = OperatorExpr(self.name, "<", value)

        # Check if we're in the middle of a chained comparison
        if expression_state.chain_expr is not None:
            # Get the first part of the chain
            left_expr = expression_state.chain_expr
            # Clear the chain state
            expression_state.chain_expr = None
            # Combine with AND
            return left_expr.__and__(expr)

        # Only store for chaining if we're in a transaction context
        if expression_state.is_capturing:
            # Store this expression for potential chaining
            expression_state.chain_expr = expr

        return expr

    def __ne__(self, value: Any) -> LogicalExpr:  # type: ignore[override]
        """Create a not equal expression.

        Args:
            value: The value to compare with

        Returns:
            An expression for inequality comparison
        """
        from neoalchemy.core.expressions.operators import OperatorExpr

        if value is None:
            return self.is_not_null()

        # Create the expression
        return OperatorExpr(self.name, "<>", value)

    def __ge__(self, value: Any) -> LogicalExpr:
        """Create a greater than or equal expression.

        Supports both direct comparisons and chained comparisons.

        Args:
            value: The value to compare with

        Returns:
            An expression for greater than or equal comparison
        """
        from neoalchemy.core.expressions.operators import OperatorExpr

        # Create the expression
        expr = OperatorExpr(self.name, ">=", value)

        # Check if we're in the middle of a chained comparison
        if expression_state.chain_expr is not None:
            # Get the first part of the chain
            left_expr = expression_state.chain_expr
            # Clear the chain state
            expression_state.chain_expr = None
            # Combine with AND
            return left_expr.__and__(expr)

        # Only store for chaining if we're in a transaction context
        if expression_state.is_capturing:
            # Store this expression for potential chaining
            expression_state.chain_expr = expr

        return expr

    def __le__(self, value: Any) -> LogicalExpr:
        """Create a less than or equal expression.

        Supports both direct comparisons and chained comparisons.

        Args:
            value: The value to compare with

        Returns:
            An expression for less than or equal comparison
        """
        from neoalchemy.core.expressions.operators import OperatorExpr

        # Create the expression
        expr = OperatorExpr(self.name, "<=", value)

        # Check if we're in the middle of a chained comparison
        if expression_state.chain_expr is not None:
            # Get the first part of the chain
            left_expr = expression_state.chain_expr
            # Clear the chain state
            expression_state.chain_expr = None
            # Combine with AND
            return left_expr.__and__(expr)

        # Only store for chaining if we're in a transaction context
        if expression_state.is_capturing:
            # Store this expression for potential chaining
            expression_state.chain_expr = expr

        return expr

    def starts_with(self, prefix: str) -> LogicalExpr:
        """Create a STARTS WITH expression.

        Args:
            prefix: Prefix to match

        Returns:
            An expression for prefix matching
        """
        from neoalchemy.core.cypher.core.keywords import CypherKeywords as K
        from neoalchemy.core.expressions.operators import OperatorExpr

        return OperatorExpr(self.name, K.STARTS_WITH, prefix)

    def startswith(self, prefix: str) -> LogicalExpr:
        """Alias for starts_with to match Python's str.startswith method.

        Args:
            prefix: Prefix to match

        Returns:
            An expression for prefix matching
        """
        return self.starts_with(prefix)

    def ends_with(self, suffix: str) -> LogicalExpr:
        """Create an ENDS WITH expression.

        Args:
            suffix: Suffix to match

        Returns:
            An expression for suffix matching
        """
        from neoalchemy.core.cypher.core.keywords import CypherKeywords as K
        from neoalchemy.core.expressions.operators import OperatorExpr

        return OperatorExpr(self.name, K.ENDS_WITH, suffix)

    def endswith(self, suffix: str) -> LogicalExpr:
        """Alias for ends_with to match Python's str.endswith method.

        Args:
            suffix: Suffix to match

        Returns:
            An expression for suffix matching
        """
        return self.ends_with(suffix)

    def in_list(self, values: List[Any]) -> LogicalExpr:
        """Create an IN expression.

        Args:
            values: List of values to check against

        Returns:
            An expression for list membership
        """
        from neoalchemy.core.cypher.core.keywords import CypherKeywords as K
        from neoalchemy.core.expressions.operators import OperatorExpr

        return OperatorExpr(self.name, K.IN, values)

    def one_of(self, *values) -> LogicalExpr:
        """Check if field is one of the given values.

        More Pythonic than in_list for variadic arguments.

        Args:
            *values: Values to check against

        Returns:
            An expression for list membership
        """
        from neoalchemy.core.expressions.operators import OperatorExpr

        return OperatorExpr(self.name, "IN", list(values))

    def between(self, min_val: Any, max_val: Any) -> LogicalExpr:
        """Check if field is between min and max values (inclusive).

        Args:
            min_val: Minimum value
            max_val: Maximum value

        Returns:
            A composite expression for range check
        """
        # We use and rather than & for logical operations
        return (self >= min_val).__and__(self <= max_val)

    def is_null(self) -> LogicalExpr:
        """Create an IS NULL expression.

        Returns:
            An expression for null check
        """
        from neoalchemy.core.expressions.operators import OperatorExpr

        return OperatorExpr(self.name, "IS NULL", None)

    def is_not_null(self) -> LogicalExpr:
        """Create an IS NOT NULL expression.

        Returns:
            An expression for non-null check
        """
        from neoalchemy.core.expressions.operators import OperatorExpr

        return OperatorExpr(self.name, "IS NOT NULL", None)

    def length(self) -> "LogicalExpr":
        """Get the length of a string or array field.

        Returns:
            A function expression for length
        """
        from neoalchemy.core.expressions.functions import FunctionExpr

        return FunctionExpr("length", [self.name])

    def len(self) -> "LogicalExpr":
        """Alias for length() that's more Pythonic.

        Returns:
            A function expression for length
        """
        return self.length()

    def __ror__(self, other: Any) -> LogicalExpr:
        """Support reversed 'in' operator (field in collection).

        This enables syntax like:
        Person.role in ["admin", "manager"]

        Args:
            other: A collection (list, tuple, set) to check membership against

        Returns:
            An expression for list membership

        Raises:
            TypeError: If the left operand is not a list, tuple, or set
        """
        if isinstance(other, (list, tuple, set)):
            return self.in_list(list(other))

        # For other types, raise a descriptive error
        raise TypeError(
            f"Unsupported 'in' operand: '{self.name} in {type(other).__name__}'. "
            f"The left operand must be a list, tuple, or set."
        )

    def lower(self) -> "LogicalExpr":
        """Convert a string field to lowercase.

        Returns:
            A function expression for lowercase conversion
        """
        from neoalchemy.core.expressions.functions import FunctionExpr

        return FunctionExpr("toLower", [self.name])

    def upper(self) -> "LogicalExpr":
        """Convert a string field to uppercase.

        Returns:
            A function expression for uppercase conversion
        """
        from neoalchemy.core.expressions.functions import FunctionExpr

        return FunctionExpr("toUpper", [self.name])
