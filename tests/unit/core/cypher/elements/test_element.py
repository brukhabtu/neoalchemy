"""
Unit tests for Cypher element base classes.

These tests focus on the abstract base classes that define the Cypher element interface.
"""

import pytest
from abc import ABC

from neoalchemy.core.cypher.elements.element import CypherElement


@pytest.mark.unit
class TestCypherElement:
    """Test the CypherElement abstract base class."""
    
    def test_cypher_element_is_abstract(self):
        """Test that CypherElement cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            CypherElement()
    
    def test_cypher_element_inheritance(self):
        """Test CypherElement can be inherited with proper implementation."""
        class ConcreteCypherElement(CypherElement):
            def to_cypher(self, params, param_index):
                return "TEST", param_index
        
        # Should be able to instantiate concrete implementation
        element = ConcreteCypherElement()
        assert isinstance(element, CypherElement)
        
        # Should have the implemented method
        result = element.to_cypher({}, 0)
        assert result == ("TEST", 0)
    
    def test_cypher_element_abstract_method_signature(self):
        """Test the abstract method has correct signature."""
        # Verify the method exists and is abstract
        assert hasattr(CypherElement, 'to_cypher')
        assert CypherElement.to_cypher.__isabstractmethod__
    
    def test_cypher_element_abstract_method_not_implemented(self):
        """Test the abstract method raises TypeError when called on incomplete subclass."""
        class IncompleteCypherElement(CypherElement):
            pass  # Missing to_cypher implementation
        
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteCypherElement()