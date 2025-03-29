"""
Core expression system for Neo4j queries.

This module defines the expression classes used to build Neo4j queries
in a Pythonic way. These expressions can be combined using Python operators
to create complex query conditions.

The expression system supports:
- Standard comparison operators (==, !=, >, <, >=, <=)
- Chained comparisons (e.g., 25 <= Person.age <= 35)
- Logical operators (and, or, not)
- Containment checks using 'in' operator (e.g., "Smith" in Person.last_name)
- String operations (starts_with, ends_with, etc.)
"""

from typing import Any, Dict, List, Optional

# Import the expression state manager from the dedicated state module
from neoalchemy.state import expression_state


class Expr:
    """Base class for all expressions."""
    
    def __and__(self, other: "Expr") -> "CompositeExpr":
        """Combine with another expression using AND.
        
        This supports the Python 'and' operator when used with parentheses:
        (expr1) and (expr2)
        
        Args:
            other: Another expression
            
        Returns:
            A composite expression with AND operator
        """
        return CompositeExpr(self, "AND", other)
        
    def __or__(self, other: "Expr") -> "CompositeExpr":
        """Combine with another expression using OR.
        
        This supports the Python 'or' operator when used with parentheses:
        (expr1) or (expr2)
        
        Args:
            other: Another expression
            
        Returns:
            A composite expression with OR operator
        """
        return CompositeExpr(self, "OR", other)
        
    def __invert__(self) -> "NotExpr":
        """Negate this expression with NOT (using the ~ operator).
        
        This allows for negating expressions with ~:
        ~expr
        
        Returns:
            A negated expression
        """
        return NotExpr(self)


class CompositeExpr(Expr):
    """A composite expression combining two expressions with an operator."""
    
    def __init__(self, left: Expr, op: str, right: Expr):
        """Initialize a composite expression.
        
        Args:
            left: Left expression
            op: Operator (AND, OR)
            right: Right expression
        """
        self.left = left
        self.op = op
        self.right = right
        
    def to_cypher(self, params: Dict[str, Any], param_index: int) -> tuple:
        """Convert to Cypher expression.
        
        Args:
            params: Parameters dictionary to populate
            param_index: Current parameter index
            
        Returns:
            Tuple of (cypher_expr, next_param_index)
        """
        left_expr, param_index = self.left.to_cypher(params, param_index)
        right_expr, param_index = self.right.to_cypher(params, param_index)
        return f"({left_expr} {self.op} {right_expr})", param_index


class NotExpr(Expr):
    """A negated expression.
    
    This is created when using the ~ operator on an expression:
    ~(Person.age > 30)  ->  NotExpr(Person.age > 30)
    """
    
    def __init__(self, expr: Expr):
        """Initialize a NOT expression.
        
        Args:
            expr: Expression to negate
        """
        self.expr = expr
        
    def to_cypher(self, params: Dict[str, Any], param_index: int) -> tuple:
        """Convert to Cypher expression.
        
        Args:
            params: Parameters dictionary to populate
            param_index: Current parameter index
            
        Returns:
            Tuple of (cypher_expr, next_param_index)
        """
        expr, param_index = self.expr.to_cypher(params, param_index)
        return f"NOT ({expr})", param_index


class FieldExpr(Expr):
    """Field expression for building conditions."""
    
    def __init__(self, name: str, array_field_types: Optional[List[str]] = None):
        """Initialize the field expression.
        
        Args:
            name: The field name in the database
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
        array_field_names = ['participants', 'keywords', 'tags', 'sources'] + self._array_field_types
        
        # Check for exact matches in known array fields
        if self.name in array_field_names:
            return True
            
        # Check for plurals (fields ending with 's')
        # This is a heuristic and might not be 100% accurate
        if self.name.endswith('s') and not self.name.endswith('ss'):  # Avoid things like 'address'
            return True
            
        return False
    
    def __contains__(self, value: Any) -> bool:
        """Create a 'contains' expression for string or array containment checks.
        
        This method enables the Pythonic 'in' operator syntax for queries by:
        1. Creating an appropriate containment expression based on field type
        2. Storing the expression in expression_state.last_expr when inside a transaction
        3. Always returning True to satisfy Python's language requirements
        
        ## How the 'in' Operator Works
        
        When you write `"Smith" in Person.last_name`, Python:
        1. Translates this to `Person.last_name.__contains__("Smith")`
        2. This method creates the appropriate expression
        3. Stores it in expression_state.last_expr if capturing is active
        4. Returns True (required by Python, otherwise 'in' wouldn't work)
        
        The query builder later retrieves the expression from expression_state
        when it processes the `where()` conditions.
        
        ## String vs. Array Containment
        
        The method intelligently creates different expressions based on field type:
        - For string fields: Uses Neo4j's CONTAINS operator (substring check)
        - For array fields: Uses Neo4j's ANY IN operator (array membership check)
        
        ## Usage Requirements
        
        Must be used inside a transaction context:
        
        ```python
        with repo.transaction() as tx:
            query = tx.query(Person).where("Smith" in Person.last_name)
            # or for array fields:
            query = tx.query(Person).where("developer" in Person.tags)
        ```
        
        Args:
            value: The value to check for containment
            
        Returns:
            Always returns True, but when inside a transaction also records the expression
        """
        # Create the appropriate expression based on field type
        if self.is_array_field():
            # For arrays/lists, use ANY IN operator in Neo4j
            expr = OperatorExpr(self.name, "ANY IN", value)
        else:
            # For strings, use CONTAINS operator
            expr = OperatorExpr(self.name, "CONTAINS", value)
        
        # Check if we're in a transaction context and record the expression if so
        if expression_state.is_capturing:
            expression_state.last_expr = expr
            
        # Always return True - this is required by the Python language
        # The query builder will retrieve the expression from expression_state later
        return True
        
    def contains(self, value: Any) -> "OperatorExpr":
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
            Operator expression for containment check
        """
        if self.is_array_field():
            # For arrays, check array membership
            return OperatorExpr(self.name, "ANY IN", value)
        else:
            # For strings, check substring containment
            return OperatorExpr(self.name, "CONTAINS", value)
    
    def __eq__(self, value: Any) -> "OperatorExpr":
        """Create an equality expression.
        
        Supports both direct comparisons and chained comparisons (e.g., 25 <= Person.age <= 35).
        
        Args:
            value: The value to compare with
            
        Returns:
            Operator expression for use in where() clauses
            
        Examples:
            # Simple equality check
            Person.age == 30
            
            # As part of a chained comparison
            25 <= Person.age <= 35  # Same as Person.age.between(25, 35)
        """
        if value is None:
            return self.is_null()
            
        # Create the expression
        expr = OperatorExpr(self.name, "=", value)
        
        # Check if we're in the middle of a chained comparison
        if expression_state.chain_expr is not None:
            # Get the first part of the chain
            left_expr = expression_state.chain_expr
            # Clear the chain state
            expression_state.chain_expr = None
            # Combine with AND
            return left_expr & expr
        
        # Only store for chaining if we're in a transaction context
        if expression_state.is_capturing:
            # Store this expression for potential chaining
            expression_state.chain_expr = expr
        
        return expr
    
    def __gt__(self, value: Any) -> "OperatorExpr":
        """Create a greater than expression.
        
        Supports both direct comparisons and chained comparisons.
        
        Args:
            value: The value to compare with
            
        Returns:
            Operator expression for use in where() clauses
            
        Examples:
            # Simple greater than check
            Person.age > 25
            
            # As part of a chained comparison
            25 < Person.age < 35  # Find people with age between 25 and 35 (exclusive)
        """
        # Create the expression
        expr = OperatorExpr(self.name, ">", value)
        
        # Check if we're in the middle of a chained comparison
        if expression_state.chain_expr is not None:
            # Get the first part of the chain
            left_expr = expression_state.chain_expr
            # Clear the chain state
            expression_state.chain_expr = None
            # Combine with AND
            return left_expr & expr
        
        # Only store for chaining if we're in a transaction context
        if expression_state.is_capturing:
            # Store this expression for potential chaining
            expression_state.chain_expr = expr
        
        return expr
    
    def __lt__(self, value: Any) -> "OperatorExpr":
        """Create a less than expression.
        
        Supports both direct comparisons and chained comparisons.
        
        Args:
            value: The value to compare with
            
        Returns:
            Operator expression for use in where() clauses
            
        Examples:
            # Simple less than check
            Person.age < 35
            
            # As part of a chained comparison
            25 < Person.age < 35  # Find people with age between 25 and 35 (exclusive)
        """
        # Create the expression
        expr = OperatorExpr(self.name, "<", value)
        
        # Check if we're in the middle of a chained comparison
        if expression_state.chain_expr is not None:
            # Get the first part of the chain
            left_expr = expression_state.chain_expr
            # Clear the chain state
            expression_state.chain_expr = None
            # Combine with AND
            return left_expr & expr
        
        # Only store for chaining if we're in a transaction context
        if expression_state.is_capturing:
            # Store this expression for potential chaining
            expression_state.chain_expr = expr
        
        return expr
    
    def __ne__(self, value: Any) -> "OperatorExpr":
        """Create a not equal expression.
        
        Args:
            value: The value to compare with
            
        Returns:
            Operator expression for use in where() clauses
            
        Examples:
            # Not equal check
            Person.name != "Alice"
            
            # Check for non-null values
            Person.email != None  # Same as Person.email.is_not_null()
        """
        if value is None:
            return self.is_not_null()
            
        # Create the expression
        expr = OperatorExpr(self.name, "<>", value)
        
        # Don't ever chain expressions with != since it's not part of standard chained comparisons
        
        return expr
    
    def __ge__(self, value: Any) -> "OperatorExpr":
        """Create a greater than or equal expression.
        
        Supports both direct comparisons and chained comparisons.
        
        Args:
            value: The value to compare with
            
        Returns:
            Operator expression for use in where() clauses
            
        Examples:
            # Simple greater than or equal check
            Person.age >= 25
            
            # As part of a chained comparison
            25 <= Person.age <= 35  # Find people with age between 25 and 35 (inclusive)
        """
        # Create the expression
        expr = OperatorExpr(self.name, ">=", value)
        
        # Check if we're in the middle of a chained comparison
        if expression_state.chain_expr is not None:
            # Get the first part of the chain
            left_expr = expression_state.chain_expr
            # Clear the chain state
            expression_state.chain_expr = None
            # Combine with AND
            return left_expr & expr
        
        # Only store for chaining if we're in a transaction context
        if expression_state.is_capturing:
            # Store this expression for potential chaining
            expression_state.chain_expr = expr
        
        return expr
    
    def __le__(self, value: Any) -> "OperatorExpr":
        """Create a less than or equal expression.
        
        Supports both direct comparisons and chained comparisons.
        
        Args:
            value: The value to compare with
            
        Returns:
            Operator expression for use in where() clauses
            
        Examples:
            # Simple less than or equal check
            Person.age <= 35
            
            # As part of a chained comparison
            25 <= Person.age <= 35  # Find people with age between 25 and 35 (inclusive)
        """
        # Create the expression
        expr = OperatorExpr(self.name, "<=", value)
        
        # Check if we're in the middle of a chained comparison
        if expression_state.chain_expr is not None:
            # Get the first part of the chain
            left_expr = expression_state.chain_expr
            # Clear the chain state
            expression_state.chain_expr = None
            # Combine with AND
            return left_expr & expr
        
        # Only store for chaining if we're in a transaction context
        if expression_state.is_capturing:
            # Store this expression for potential chaining
            expression_state.chain_expr = expr
        
        return expr
    
    def starts_with(self, prefix: str) -> "OperatorExpr":
        """Create a STARTS WITH expression.
        
        Args:
            prefix: Prefix to match
            
        Returns:
            Operator expression
        """
        return OperatorExpr(self.name, "STARTS WITH", prefix)
        
    def startswith(self, prefix: str) -> "OperatorExpr":
        """Alias for starts_with to match Python's str.startswith method.
        
        This provides a more Pythonic interface that matches Python's standard
        string method names.
        
        Args:
            prefix: Prefix to match
            
        Returns:
            Operator expression
            
        Example:
            # Find names starting with 'A'
            tx.query(Person).where(Person.name.startswith("A")).find()
        """
        return self.starts_with(prefix)
    
    def ends_with(self, suffix: str) -> "OperatorExpr":
        """Create an ENDS WITH expression.
        
        Args:
            suffix: Suffix to match
            
        Returns:
            Operator expression
        """
        return OperatorExpr(self.name, "ENDS WITH", suffix)
        
    def endswith(self, suffix: str) -> "OperatorExpr":
        """Alias for ends_with to match Python's str.endswith method.
        
        This provides a more Pythonic interface that matches Python's standard
        string method names.
        
        Args:
            suffix: Suffix to match
            
        Returns:
            Operator expression
            
        Example:
            # Find emails ending with .com domain
            tx.query(Person).where(Person.email.endswith(".com")).find()
        """
        return self.ends_with(suffix)
    
    def in_list(self, values: List[Any]) -> "OperatorExpr":
        """Create an IN expression.
        
        Args:
            values: List of values to check against
            
        Returns:
            Operator expression
        """
        return OperatorExpr(self.name, "IN", values)
    
    def one_of(self, *values) -> "OperatorExpr":
        """Check if field is one of the given values (more Pythonic than in_list).
        
        Args:
            *values: Values to check against
            
        Returns:
            Operator expression
        """
        return OperatorExpr(self.name, "IN", list(values))
    
    def between(self, min_val: Any, max_val: Any) -> "CompositeExpr":
        """Check if field is between min and max values (inclusive).
        
        This is an explicit method alternative to Python's chained comparison.
        Both `field.between(min_val, max_val)` and `min_val <= field <= max_val`
        produce the same result.
        
        Args:
            min_val: Minimum value
            max_val: Maximum value
            
        Returns:
            Composite expression
            
        Examples:
            # These two expressions are equivalent:
            Person.age.between(25, 35)
            25 <= Person.age <= 35
        """
        return (self >= min_val) & (self <= max_val)
    
    def is_null(self) -> "OperatorExpr":
        """Create an IS NULL expression.
        
        Returns:
            Operator expression
        """
        return OperatorExpr(self.name, "IS NULL", None)
    
    def is_not_null(self) -> "OperatorExpr":
        """Create an IS NOT NULL expression.
        
        Returns:
            Operator expression
        """
        return OperatorExpr(self.name, "IS NOT NULL", None)
    
    def length(self) -> "FunctionExpr":
        """Get the length of a string or array field.
        
        Returns:
            Function expression
        """
        return FunctionExpr("length", [self.name])
    
    def len(self) -> "FunctionExpr":
        """Get the length of a string or array field (more Pythonic than length).
        
        Returns:
            Function expression
        """
        return self.length()
        
    def __ror__(self, other: Any) -> "OperatorExpr":
        """Support reversed 'in' operator (field in collection).
        
        This method enables a more intuitive syntax for checking if a field's value
        is in a collection of values:
        
        ```python
        # Check if person's role is either "admin" or "manager"
        Person.role in ["admin", "manager"]
        ```
        
        Which is equivalent to:
        ```python
        Person.role.one_of("admin", "manager")
        ```
        
        Args:
            other: A collection (list, tuple, set) to check membership against
            
        Returns:
            An expression for use in query conditions
            
        Raises:
            TypeError: If the left operand is not a list, tuple, or set
        """
        if isinstance(other, (list, tuple, set)):
            return self.in_list(list(other))
        
        # For other types, raise a descriptive error
        raise TypeError(f"Unsupported 'in' operand: '{self.name} in {type(other).__name__}'. "
                        f"The left operand must be a list, tuple, or set.")
    
    def lower(self) -> "FunctionExpr":
        """Convert a string field to lowercase.
        
        Returns:
            Function expression
        """
        return FunctionExpr("toLower", [self.name])
    
    def upper(self) -> "FunctionExpr":
        """Convert a string field to uppercase.
        
        Returns:
            Function expression
        """
        return FunctionExpr("toUpper", [self.name])
    
    def to_cypher(self, params: Dict[str, Any], param_index: int) -> tuple:
        """Convert to Cypher expression (just the field name).
        
        Args:
            params: Parameters dictionary to populate
            param_index: Current parameter index
            
        Returns:
            Tuple of (cypher_expr, next_param_index)
        """
        return f"e.{self.name}", param_index


class OperatorExpr(Expr):
    """An expression with an operator (e.g., field = value)."""
    
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
        
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"OperatorExpr({self.field} {self.operator} {repr(self.value)})"
    
    def to_cypher(self, params: Dict[str, Any], param_index: int) -> tuple:
        """Convert to Cypher expression.
        
        Args:
            params: Parameters dictionary to populate
            param_index: Current parameter index
            
        Returns:
            Tuple of (cypher_expr, next_param_index)
        """
        param_name = f"p{param_index}"
        
        # Handle special operators that don't use parameters
        if self.operator == "IS NULL":
            return f"e.{self.field} IS NULL", param_index
        elif self.operator == "IS NOT NULL":
            return f"e.{self.field} IS NOT NULL", param_index
        
        # Special case for Neo4j array operations 
        elif self.operator == "ANY IN":
            # For Neo4j, use the 'ANY' operator on arrays
            # https://neo4j.com/docs/cypher-manual/current/syntax/operators/#query-operators-list
            params[param_name] = self.value
            # "ANY (item IN e.array_field WHERE item = $param)"
            return f"ANY (item IN e.{self.field} WHERE item = ${param_name})", param_index + 1
        
        # Regular operators with parameters
        params[param_name] = self.value
        return f"e.{self.field} {self.operator} ${param_name}", param_index + 1


class FunctionExpr(Expr):
    """A function expression (e.g., length(field))."""
    
    def __init__(self, func_name: str, args: List[Any]):
        """Initialize a function expression.
        
        Args:
            func_name: Function name
            args: Function arguments
        """
        self.func_name = func_name
        self.args = args
    
    def __eq__(self, value: Any) -> "CompositeExpr":
        """Compare function result with a value.
        
        Args:
            value: Value to compare with
            
        Returns:
            Composite expression
        """
        return FunctionComparisonExpr(self, "=", value)
    
    def __gt__(self, value: Any) -> "CompositeExpr":
        """Compare function result with a value (greater than).
        
        Args:
            value: Value to compare with
            
        Returns:
            Composite expression
        """
        return FunctionComparisonExpr(self, ">", value)
    
    def __lt__(self, value: Any) -> "CompositeExpr":
        """Compare function result with a value (less than).
        
        Args:
            value: Value to compare with
            
        Returns:
            Composite expression
        """
        return FunctionComparisonExpr(self, "<", value)
    
    def to_cypher(self, params: Dict[str, Any], param_index: int) -> tuple:
        """Convert to Cypher expression.
        
        Args:
            params: Parameters dictionary to populate
            param_index: Current parameter index
            
        Returns:
            Tuple of (cypher_expr, next_param_index)
        """
        # Handle field name arguments
        args_str = []
        for arg in self.args:
            if isinstance(arg, str) and not arg.startswith("$"):  # It's a field name
                args_str.append(f"e.{arg}")
            else:
                # It's a value that needs a parameter
                param_name = f"p{param_index}"
                params[param_name] = arg
                args_str.append(f"${param_name}")
                param_index += 1
                
        # Use toLower, toUpper instead of lower, upper for Neo4j compatibility
        func_name = self.func_name
        if func_name == "lower":
            func_name = "toLower"
        elif func_name == "upper":
            func_name = "toUpper"
                
        return f"{func_name}({', '.join(args_str)})", param_index


class FunctionComparisonExpr(Expr):
    """A comparison involving a function expression."""
    
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
    
    def to_cypher(self, params: Dict[str, Any], param_index: int) -> tuple:
        """Convert to Cypher expression.
        
        Args:
            params: Parameters dictionary to populate
            param_index: Current parameter index
            
        Returns:
            Tuple of (cypher_expr, next_param_index)
        """
        func_str, param_index = self.func_expr.to_cypher(params, param_index)
        param_name = f"p{param_index}"
        params[param_name] = self.value
        return f"{func_str} {self.operator} ${param_name}", param_index + 1