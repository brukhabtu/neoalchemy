"""
Adapter module for converting between expressions and cypher elements.

This module provides the necessary adapters to convert high-level expression
objects to low-level cypher elements, ensuring proper separation of concerns.
"""

from typing import Dict, Any

from neoalchemy.core.cypher import (
    ComparisonElement, CypherElement, FunctionCallElement, 
    LogicalElement, NegationElement, PropertyRef
)
from neoalchemy.core.expressions.base import Expr
from neoalchemy.core.expressions.fields import FieldExpr
from neoalchemy.core.expressions.functions import FunctionExpr, FunctionComparisonExpr
from neoalchemy.core.expressions.operators import OperatorExpr, CompositeExpr, NotExpr


class ExpressionAdapter:
    """Adapter for converting expressions to cypher elements.
    
    This class centralizes the conversion logic, removing the need for
    expression classes to directly depend on specific cypher implementations.
    """
    
    def __init__(self, entity_var: str = 'e'):
        """Initialize the adapter.
        
        Args:
            entity_var: The variable name to use for entity properties
        """
        self.entity_var = entity_var
    
    def to_cypher_element(self, expr: Expr) -> CypherElement:
        """Convert any expression to the appropriate cypher element.
        
        Args:
            expr: The expression to convert
            
        Returns:
            A CypherElement representation of the expression
            
        Raises:
            TypeError: If the expression type is not supported
        """
        # Dispatch to the appropriate conversion method based on type
        if isinstance(expr, FieldExpr):
            return self._convert_field_expr(expr)
        elif isinstance(expr, OperatorExpr):
            return self._convert_operator_expr(expr)
        elif isinstance(expr, CompositeExpr):
            return self._convert_composite_expr(expr)
        elif isinstance(expr, NotExpr):
            return self._convert_not_expr(expr)
        elif isinstance(expr, FunctionExpr):
            return self._convert_function_expr(expr)
        elif isinstance(expr, FunctionComparisonExpr):
            return self._convert_function_comparison_expr(expr)
        else:
            raise TypeError(f"Unsupported expression type: {type(expr).__name__}")
    
    def _convert_field_expr(self, expr: FieldExpr) -> CypherElement:
        """Convert a field expression to a cypher element.
        
        Args:
            expr: The field expression
            
        Returns:
            A PropertyRef for the field
        """
        return PropertyRef(self.entity_var, expr.name)
    
    def _convert_operator_expr(self, expr: OperatorExpr) -> CypherElement:
        """Convert an operator expression to a cypher element.
        
        Args:
            expr: The operator expression
            
        Returns:
            A ComparisonElement for the operation
        """
        # Create a PropertyRef for the field
        property_ref = PropertyRef(self.entity_var, expr.field)
        
        # Create a ComparisonElement with the property and value
        return ComparisonElement(
            property_ref, 
            expr.operator, 
            expr.value
        )
    
    def _convert_composite_expr(self, expr: CompositeExpr) -> CypherElement:
        """Convert a composite expression to a cypher element.
        
        Args:
            expr: The composite expression
            
        Returns:
            A LogicalElement combining the left and right expressions
        """
        # Convert both expressions to CypherElements
        left_element = self.to_cypher_element(expr.left)
        right_element = self.to_cypher_element(expr.right)
        
        # Create a LogicalElement with the two elements
        return LogicalElement(
            left_element,
            expr.op,
            right_element
        )
    
    def _convert_not_expr(self, expr: NotExpr) -> CypherElement:
        """Convert a NOT expression to a cypher element.
        
        Args:
            expr: The NOT expression
            
        Returns:
            A NegationElement for the expression
        """
        # Convert the expression to a CypherElement
        expr_element = self.to_cypher_element(expr.expr)
        
        # Create a NegationElement with the expression
        return NegationElement(expr_element)
    
    def _convert_function_expr(self, expr: FunctionExpr) -> CypherElement:
        """Convert a function expression to a cypher element.
        
        Args:
            expr: The function expression
            
        Returns:
            A FunctionCallElement for the function
        """
        # Process arguments to convert field names to PropertyRefs
        processed_args = []
        for arg in expr.args:
            # Check if this is a field name that needs to be converted to a PropertyRef
            if isinstance(arg, str) and self._is_field_name(arg):
                processed_args.append(PropertyRef(self.entity_var, arg))
            else:
                processed_args.append(arg)
        
        # Create a FunctionCallElement with the function name and arguments
        return FunctionCallElement(expr.func_name, processed_args)
        
    def _is_field_name(self, value: str) -> bool:
        """Determine if a string value should be treated as a field name.
        
        This method encapsulates the logic for determining whether a string
        represents a field name (that should be converted to a PropertyRef)
        or a literal value/parameter reference.
        
        Args:
            value: The string value to check
            
        Returns:
            True if the value should be treated as a field name
        """
        # Don't treat values that look like parameters as field names
        # This is intentionally abstracted to avoid Cypher-specific knowledge here
        if value.startswith('$') or value.startswith(':') or value.startswith('?'):
            return False
            
        # Don't treat quoted strings as field names
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            return False
            
        # Additional checks could be added here, e.g., for numeric literals
        
        # Default to treating it as a field name
        return True
    
    def _convert_function_comparison_expr(self, expr: FunctionComparisonExpr) -> CypherElement:
        """Convert a function comparison expression to a cypher element.
        
        Args:
            expr: The function comparison expression
            
        Returns:
            A ComparisonElement for the function comparison
        """
        # Convert the function expression to a CypherElement
        func_element = self.to_cypher_element(expr.func_expr)
        
        # Create a ComparisonElement with the function and value
        return ComparisonElement(
            func_element,
            expr.operator,
            expr.value
        )