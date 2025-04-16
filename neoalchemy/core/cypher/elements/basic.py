"""
Basic element classes for Neo4j Cypher queries.

This module provides the foundational element classes for building Cypher
queries, including property references, comparisons, and function calls.
"""

from typing import Any, Dict, List, Tuple

from neoalchemy.core.cypher.elements.element import CypherElement
from neoalchemy.core.cypher.core.keywords import CypherKeywords as K


class PropertyRef(CypherElement):
    """Represents a property reference in a Cypher query.
    
    Examples:
        n.name
        r.since
    """
    
    def __init__(self, variable: str, property_name: str):
        """Initialize a property reference.
        
        Args:
            variable: The variable name (node or relationship)
            property_name: The property name to reference
        """
        self.variable = variable
        self.property_name = property_name
    
    def to_cypher(self, params: Dict[str, Any], param_index: int) -> Tuple[str, int]:
        """Convert to Cypher property reference.
        
        Args:
            params: Parameters dictionary to populate
            param_index: Current parameter index
            
        Returns:
            Tuple of (cypher_expr, next_param_index)
        """
        return f"{self.variable}.{self.property_name}", param_index


class ComparisonElement(CypherElement):
    """Represents a comparison in a Cypher query.
    
    Examples:
        n.age > 30
        r.since = date('2020-01-01')
    """
    
    def __init__(self, left: CypherElement, operator: str, right: Any):
        """Initialize a comparison element.
        
        Args:
            left: Left side of the comparison (usually a PropertyRef)
            operator: Comparison operator (=, >, <, etc.)
            right: Right side of the comparison (usually a value)
        """
        self.left = left
        self.operator = operator
        self.right = right
    
    def to_cypher(self, params: Dict[str, Any], param_index: int) -> Tuple[str, int]:
        """Convert to Cypher comparison.
        
        Args:
            params: Parameters dictionary to populate
            param_index: Current parameter index
            
        Returns:
            Tuple of (cypher_expr, next_param_index)
        """
        # Convert the left side to Cypher
        left_str, param_index = self.left.to_cypher(params, param_index)
        
        # Handle special operators that don't use parameters
        if self.operator == K.IS_NULL:
            return f"{left_str} {K.IS_NULL}", param_index
        elif self.operator == K.IS_NOT_NULL:
            return f"{left_str} {K.IS_NOT_NULL}", param_index
        elif self.operator == K.ANY_IN:
            # For Neo4j, use the 'ANY' operator on arrays
            # https://neo4j.com/docs/cypher-manual/current/syntax/operators/#query-operators-list
            param_name = f"p{param_index}"
            params[param_name] = self.right
            # "ANY (item IN e.array_field WHERE item = $param)"
            return f"ANY (item IN {left_str} WHERE item {K.EQUALS} ${param_name})", param_index + 1
        
        # Regular comparison with parameter
        param_name = f"p{param_index}"
        params[param_name] = self.right
        return f"{left_str} {self.operator} ${param_name}", param_index + 1


class LogicalElement(CypherElement):
    """Represents a logical operation in a Cypher query.
    
    Examples:
        n.age > 30 AND n.name = 'Alice'
        r.since < date('2020-01-01') OR r.active = true
    """
    
    def __init__(self, left: CypherElement, operator: str, right: CypherElement):
        """Initialize a logical element.
        
        Args:
            left: Left side of the logical operation
            operator: Logical operator (AND, OR)
            right: Right side of the logical operation
        """
        self.left = left
        self.operator = operator
        self.right = right
    
    def to_cypher(self, params: Dict[str, Any], param_index: int) -> Tuple[str, int]:
        """Convert to Cypher logical operation.
        
        Args:
            params: Parameters dictionary to populate
            param_index: Current parameter index
            
        Returns:
            Tuple of (cypher_expr, next_param_index)
        """
        # Convert both sides to Cypher
        left_str, param_index = self.left.to_cypher(params, param_index)
        right_str, param_index = self.right.to_cypher(params, param_index)
        
        # Combine with the logical operator
        return f"({left_str} {self.operator} {right_str})", param_index


class NegationElement(CypherElement):
    """Represents a logical negation in a Cypher query.
    
    Examples:
        NOT (n.age > 30)
        NOT (n.name = 'Alice')
    """
    
    def __init__(self, expr: CypherElement):
        """Initialize a negation element.
        
        Args:
            expr: Expression to negate
        """
        self.expr = expr
    
    def to_cypher(self, params: Dict[str, Any], param_index: int) -> Tuple[str, int]:
        """Convert to Cypher negation.
        
        Args:
            params: Parameters dictionary to populate
            param_index: Current parameter index
            
        Returns:
            Tuple of (cypher_expr, next_param_index)
        """
        # Convert the expression to Cypher
        expr_str, param_index = self.expr.to_cypher(params, param_index)
        
        # Add the NOT operator
        return f"{K.NOT} ({expr_str})", param_index


class FunctionCallElement(CypherElement):
    """Represents a function call in a Cypher query.
    
    Examples:
        length(n.name)
        toUpper(n.email)
    """
    
    def __init__(self, function_name: str, args: List[Any]):
        """Initialize a function call element.
        
        Args:
            function_name: Name of the function to call
            args: Arguments to pass to the function
        """
        self.function_name = function_name
        self.args = args
    
    def to_cypher(self, params: Dict[str, Any], param_index: int) -> Tuple[str, int]:
        """Convert to Cypher function call.
        
        Args:
            params: Parameters dictionary to populate
            param_index: Current parameter index
            
        Returns:
            Tuple of (cypher_expr, next_param_index)
        """
        # Handle function name mapping
        func_name = self.function_name
        if func_name == "lower":
            func_name = K.TO_LOWER
        elif func_name == "upper":
            func_name = K.TO_UPPER
        
        # Process arguments
        arg_strs = []
        for arg in self.args:
            if isinstance(arg, CypherElement):
                # If it's a CypherElement, convert it
                arg_str, param_index = arg.to_cypher(params, param_index)
                arg_strs.append(arg_str)
            else:
                # If it's a value, add a parameter
                param_name = f"p{param_index}"
                params[param_name] = arg
                arg_strs.append(f"${param_name}")
                param_index += 1
        
        # Build the function call
        return f"{func_name}({', '.join(arg_strs)})", param_index