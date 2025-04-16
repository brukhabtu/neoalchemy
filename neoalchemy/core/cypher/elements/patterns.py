"""
Pattern element classes for Neo4j Cypher queries.

This module provides element classes for representing node patterns,
relationship patterns, and path patterns in Cypher queries.
"""

from typing import Any, Dict, List, Optional, Tuple

from neoalchemy.core.cypher.elements.element import CypherElement


class NodePattern(CypherElement):
    """Represents a node pattern in a Cypher query.
    
    Examples:
        (n)
        (p:Person)
        (p:Person:Customer)
        (p:Person {name: $name})
    """
    
    def __init__(self, 
                 variable: str, 
                 labels: Optional[List[str]] = None,
                 properties: Optional[Dict[str, Any]] = None):
        """Initialize a node pattern.
        
        Args:
            variable: Variable name for the node
            labels: Optional list of node labels
            properties: Optional dictionary of property constraints
        """
        self.variable = variable
        self.labels = labels or []
        self.properties = properties or {}
    
    def to_cypher(self, params: Dict[str, Any], param_index: int) -> Tuple[str, int]:
        """Convert to Cypher node pattern.
        
        Args:
            params: Parameters dictionary to populate
            param_index: Current parameter index
            
        Returns:
            Tuple of (cypher_expr, next_param_index)
        """
        # Build the variable and labels part
        pattern = self.variable
        if self.labels:
            labels_str = "".join(f":{label}" for label in self.labels)
            pattern += labels_str
        
        # Add properties if any
        if self.properties:
            # Create a new parameter for the properties
            param_name = f"p{param_index}"
            params[param_name] = self.properties
            pattern += f" {{${param_name}}}"
            param_index += 1
        
        # Wrap in parentheses
        return f"({pattern})", param_index


class RelationshipPattern(CypherElement):
    """Represents a relationship pattern in a Cypher query.
    
    Examples:
        -[r]-
        -[r:KNOWS]->
        -[r:WORKS_AT {since: 2020}]->
    """
    
    def __init__(self,
                 variable: str,
                 types: Optional[List[str]] = None,
                 properties: Optional[Dict[str, Any]] = None,
                 direction: str = "->"):
        """Initialize a relationship pattern.
        
        Args:
            variable: Variable name for the relationship
            types: Optional list of relationship types
            properties: Optional dictionary of property constraints
            direction: Direction of the relationship ("->" for outgoing,
                      "<-" for incoming, "-" for undirected)
        """
        self.variable = variable
        self.types = types or []
        self.properties = properties or {}
        
        # Validate direction
        if direction not in ["->", "<-", "-"]:
            raise ValueError("Direction must be one of: '->', '<-', '-'")
        self.direction = direction
    
    def to_cypher(self, params: Dict[str, Any], param_index: int) -> Tuple[str, int]:
        """Convert to Cypher relationship pattern.
        
        Args:
            params: Parameters dictionary to populate
            param_index: Current parameter index
            
        Returns:
            Tuple of (cypher_expr, next_param_index)
        """
        # Build the variable and types part
        pattern = self.variable
        if self.types:
            types_str = "|".join(self.types)
            pattern += f":{types_str}"
        
        # Add properties if any
        if self.properties:
            # Create a new parameter for the properties
            param_name = f"p{param_index}"
            params[param_name] = self.properties
            pattern += f" {{${param_name}}}"
            param_index += 1
        
        # Determine start and end based on direction
        if self.direction == "->":
            return f"-[{pattern}]->", param_index
        elif self.direction == "<-":
            return f"<-[{pattern}]-", param_index
        else:  # undirected
            return f"-[{pattern}]-", param_index


class PathPattern(CypherElement):
    """Represents a path pattern in a Cypher query.
    
    Examples:
        (p:Person)-[r:KNOWS]->(f:Person)
        (p:Person)<-[r:WORKS_AT]-(c:Company)
    """
    
    def __init__(self,
                 start_node: NodePattern,
                 relationship: RelationshipPattern,
                 end_node: NodePattern):
        """Initialize a path pattern.
        
        Args:
            start_node: Starting node pattern
            relationship: Relationship pattern
            end_node: Ending node pattern
        """
        self.start_node = start_node
        self.relationship = relationship
        self.end_node = end_node
    
    def to_cypher(self, params: Dict[str, Any], param_index: int) -> Tuple[str, int]:
        """Convert to Cypher path pattern.
        
        Args:
            params: Parameters dictionary to populate
            param_index: Current parameter index
            
        Returns:
            Tuple of (cypher_expr, next_param_index)
        """
        # Convert the parts to Cypher
        start_str, param_index = self.start_node.to_cypher(params, param_index)
        rel_str, param_index = self.relationship.to_cypher(params, param_index)
        end_str, param_index = self.end_node.to_cypher(params, param_index)
        
        # Combine the pattern parts
        return f"{start_str}{rel_str}{end_str}", param_index