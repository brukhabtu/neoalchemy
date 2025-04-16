"""
Base classes for the Cypher query system.

This module defines the fundamental abstract base classes that all
Cypher components extend.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple


class CypherElement(ABC):
    """Base class for all Cypher query elements.
    
    This class defines the interface that all Cypher elements must implement,
    particularly the ability to be compiled into a Cypher string with parameters.
    """
    
    @abstractmethod
    def to_cypher(self, params: Dict[str, Any], param_index: int) -> Tuple[str, int]:
        """Convert element to Cypher expression.
        
        This low-level method is used by the compilation process to build
        a complete Cypher query with proper parameter bindings.
        
        Args:
            params: Parameters dictionary to populate with values
            param_index: Current parameter index for generating unique parameter names
            
        Returns:
            Tuple of (cypher_expr, next_param_index)
        """
        pass
    
