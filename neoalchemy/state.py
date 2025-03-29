"""
Thread-local state management for NeoAlchemy's expression system.

This module provides a clean interface for managing thread-local state in NeoAlchemy,
specifically focusing on expression capturing and state management across transactions.

## Expression State System

NeoAlchemy uses thread-local state to support Pythonic syntax for:
1. Containment checks using the 'in' operator (`"Smith" in Person.last_name`)
2. Chained comparisons (`25 <= Person.age <= 35`)

The expression state system works through these key components:

1. **Thread-local storage**: Ensures concurrency safety when multiple threads execute
   transactions simultaneously.

2. **Transaction boundary state management**: The Neo4jTransaction `__enter__` and
   `__exit__` methods manage state transitions by calling:
   - `expression_state.start_capturing()` when a transaction begins
   - `expression_state.stop_capturing()` when a transaction ends

3. **Expression Capture Mechanism**:
   - The `is_capturing` flag controls whether expressions should be captured
   - For 'in' operator: The `__contains__` method of FieldExpr stores expressions 
     in `last_expr` when `is_capturing` is True
   - For chained comparisons: Comparison operator methods (like `__le__`) store
     intermediate expressions in `chain_expr`

## Lifecycle of an Expression

1. User begins a transaction:
   ```python
   with repo.transaction() as tx:
       # expression_state.start_capturing() called during __enter__
   ```

2. User creates an expression using Pythonic syntax:
   ```python
   tx.query(Person).where("Smith" in Person.last_name)  # Capture happens here
   ```

3. Internal capture process:
   - The `in` operator calls `Person.last_name.__contains__("Smith")`
   - `__contains__` method checks if `is_capturing` is True
   - If capturing, it creates and stores the expression in `last_expr`
   - Returns True to satisfy Python's language requirements

4. Query state retrieval:
   - The `where()` method retrieves the stored expression from `last_expr`
   - It resets the state to avoid accidental reuse

5. Transaction ends:
   ```python
   # expression_state.stop_capturing() called during __exit__
   ```

This state management system enables a clean Pythonic API while handling the
state transitions and cleanup transparently to the user.
"""

import threading
from typing import Any, Optional


class ExpressionState:
    """Manages thread-local state for expression capturing and evaluation.
    
    This class is the core of NeoAlchemy's expression capture system. It manages
    thread-local state to enable Pythonic syntax for queries while maintaining 
    thread safety for concurrent operations.
    
    The class provides state management for two key language features:
    1. Capturing expressions with the 'in' operator (string and array containment)
    2. Supporting chained comparisons (e.g., 25 <= Person.age <= 35)
    
    ## Thread Safety
    
    Each thread has its own isolated state, allowing multiple transactions to operate
    concurrently without interference. The thread-local storage ensures that expression
    capturing in one thread doesn't affect other threads.
    
    ## State Variables
    
    The class manages three primary state variables:
    - `capturing`: Boolean flag indicating if expressions should be captured
    - `last_expr`: Stores the expression from the most recent 'in' operator use
    - `chain_expr`: Stores the left side of a chained comparison operation
    
    ## Usage Pattern
    
    The ExpressionState is used within a transaction context:
    
    ```python
    # Transaction begins
    expression_state.start_capturing()  # Enables expression capture
    
    # User code executes expressions
    # - Expressions are captured in last_expr or chain_expr
    
    # Query builder retrieves captured expressions
    expr = expression_state.last_expr
    expression_state.last_expr = None  # Reset state after use
    
    # Transaction ends
    expression_state.stop_capturing()  # Cleans up all state
    ```
    
    This pattern ensures that state is properly managed throughout the transaction
    lifecycle and allows for natural Python syntax in query expressions.
    """
    
    def __init__(self):
        """Initialize the expression state manager."""
        self._state = threading.local()
        # Initialize with default values to avoid hasattr checks
        self.reset()
    
    def reset(self):
        """Reset all state to default values.
        
        This method sets all state variables to their default values:
        - capturing: False (disables expression capture)
        - last_expr: None (clears any captured 'in' operator expressions)
        - chain_expr: None (clears any chained comparison state)
        
        This is called automatically by other methods like start_capturing()
        and stop_capturing(), but can also be called directly to reset state
        in exceptional circumstances.
        """
        self._state.capturing = False
        self._state.last_expr = None  # For 'in' operator
        self._state.chain_expr = None  # For chained comparisons
    
    def start_capturing(self):
        """Start capturing expressions for a transaction.
        
        This method should be called at the beginning of a transaction context
        to enable expression capture. It performs these steps:
        
        1. Resets all state to ensure a clean starting point
        2. Enables expression capturing by setting capturing=True
        
        After this method is called, the 'in' operator and chained comparison
        expressions will be captured when used within the current thread.
        
        Typical usage (in Neo4jTransaction.__enter__):
        ```python
        def __enter__(self):
            # Start Neo4j transaction
            # ...
            
            # Enable expression capture
            expression_state.start_capturing()
            
            return self
        ```
        """
        self.reset()  # Start with clean state
        self._state.capturing = True
    
    def stop_capturing(self):
        """Stop capturing expressions and clean up state.
        
        This method should be called at the end of a transaction context
        to disable expression capture and clean up any lingering state.
        It effectively resets all state variables to their default values.
        
        It's important to call this method even if the transaction fails
        or an exception occurs, to ensure proper state cleanup.
        
        Typical usage (in Neo4jTransaction.__exit__):
        ```python
        def __exit__(self, exc_type, exc_val, exc_tb):
            try:
                # Commit or rollback transaction
                # ...
            finally:
                # Clean up resources
                # ...
                
                # Stop capturing expressions and clean up state
                expression_state.stop_capturing()
        ```
        """
        self.reset()
    
    @property
    def is_capturing(self) -> bool:
        """Check if expression capturing is active.
        
        Returns:
            bool: True if expression capturing is currently active, False otherwise.
            
        This property is used to determine whether expressions should be captured
        when operators like 'in' or comparison operators are used. It's controlled
        by the start_capturing() and stop_capturing() methods.
        
        Usage example in field expressions:
        ```python
        def __contains__(self, value: Any) -> bool:
            # Create the expression
            expr = OperatorExpr(self.name, "CONTAINS", value)
            
            # Only capture the expression if capturing is active
            if expression_state.is_capturing:
                expression_state.last_expr = expr
                
            return True
        ```
        """
        return self._state.capturing
    
    @property
    def last_expr(self) -> Optional[Any]:
        """Get the last expression from the 'in' operator.
        
        Returns:
            Optional[Expr]: The last expression captured from the 'in' operator,
                           or None if no expression has been captured.
        
        This property stores expressions created by the 'in' operator when used
        with field expressions, like `"Smith" in Person.last_name`. It's used by
        the query builder to retrieve the expression after the 'in' operator
        has been evaluated.
        
        The typical lifecycle is:
        1. User code executes an 'in' expression
        2. FieldExpr.__contains__ stores the expression in last_expr
        3. QueryBuilder.where() retrieves the expression and clears last_expr
        """
        return self._state.last_expr
    
    @last_expr.setter
    def last_expr(self, expr: Optional[Any]):
        """Store the last expression from the 'in' operator.
        
        Args:
            expr: The expression to store, or None to clear the stored expression.
            
        This setter is primarily used by the FieldExpr.__contains__ method to store
        expressions created by the 'in' operator, and by the QueryBuilder.where()
        method to clear the stored expression after retrieving it.
        """
        self._state.last_expr = expr
    
    @property
    def chain_expr(self) -> Optional[Any]:
        """Get the stored chain expression for chained comparisons.
        
        Returns:
            Optional[Expr]: The first part of a chained comparison,
                           or None if no chained comparison is in progress.
                           
        This property stores the left side of a chained comparison expression
        like `25 <= Person.age <= 35`. It's used to temporarily hold the first
        comparison (`25 <= Person.age`) until the second comparison (`Person.age <= 35`)
        is evaluated.
        
        The typical lifecycle for a chained comparison is:
        1. First comparison stores its expression in chain_expr
        2. Second comparison retrieves chain_expr, combines it with its own expression,
           and clears chain_expr
        """
        return self._state.chain_expr
    
    @chain_expr.setter
    def chain_expr(self, expr: Optional[Any]):
        """Store an expression for chained comparison.
        
        Args:
            expr: The expression to store, or None to clear the stored expression.
            
        This setter is used by comparison methods like __le__, __ge__, etc. to store
        and retrieve the left side of a chained comparison. Setting it to None clears
        the stored expression, which happens when the chained comparison is complete
        or when cleaning up state.
        """
        self._state.chain_expr = expr


# Singleton instance of the expression state manager
expression_state = ExpressionState()