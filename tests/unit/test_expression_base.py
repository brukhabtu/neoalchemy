"""
Unit tests for expression base classes.

These tests focus on the base Expr class functionality.
"""

import pytest
from unittest.mock import Mock, patch

from neoalchemy.core.expressions.base import Expr


@pytest.mark.unit
class TestExprBase:
    """Test the base Expr class functionality."""
    
    def setUp(self):
        """Reset adapter state before each test."""
        Expr._adapter = None
    
    def tearDown(self):
        """Reset adapter state after each test."""
        Expr._adapter = None
    
    def test_expr_class_adapter_default_none(self):
        """Test Expr class adapter is None by default."""
        # Reset to ensure clean state
        Expr._adapter = None
        
        assert Expr._adapter is None
    
    def test_get_adapter_creates_default_when_none(self):
        """Test get_adapter creates default ExpressionAdapter when none exists."""
        # Reset adapter to None
        Expr._adapter = None
        
        with patch('neoalchemy.core.expressions.adapter.ExpressionAdapter') as mock_adapter_class:
            mock_adapter_instance = Mock()
            mock_adapter_class.return_value = mock_adapter_instance
            
            result = Expr.get_adapter()
            
            # Should create new ExpressionAdapter
            mock_adapter_class.assert_called_once()
            # Should store it in class variable
            assert Expr._adapter == mock_adapter_instance
            # Should return the instance
            assert result == mock_adapter_instance
    
    def test_get_adapter_returns_existing_when_set(self):
        """Test get_adapter returns existing adapter when already set."""
        mock_adapter = Mock()
        Expr._adapter = mock_adapter
        
        result = Expr.get_adapter()
        
        # Should return existing adapter without creating new one
        assert result == mock_adapter
        assert Expr._adapter == mock_adapter
    
    def test_set_adapter_stores_adapter(self):
        """Test set_adapter stores the provided adapter."""
        mock_adapter = Mock()
        
        Expr.set_adapter(mock_adapter)
        
        # Should store the adapter in class variable
        assert Expr._adapter == mock_adapter
    
    def test_set_adapter_replaces_existing(self):
        """Test set_adapter replaces existing adapter."""
        old_adapter = Mock()
        new_adapter = Mock()
        
        # Set initial adapter
        Expr._adapter = old_adapter
        
        # Replace with new adapter
        Expr.set_adapter(new_adapter)
        
        # Should replace with new adapter
        assert Expr._adapter == new_adapter
        assert Expr._adapter != old_adapter
    
    def test_to_cypher_element_uses_adapter(self):
        """Test to_cypher_element uses the adapter to convert expressions."""
        mock_adapter = Mock()
        mock_element = Mock()
        mock_adapter.to_cypher_element.return_value = mock_element
        
        # Set up adapter
        Expr._adapter = mock_adapter
        
        # Create expression instance
        expr = Expr()
        
        result = expr.to_cypher_element()
        
        # Should call adapter with self
        mock_adapter.to_cypher_element.assert_called_once_with(expr)
        # Should return adapter result
        assert result == mock_element
    
    def test_to_cypher_element_gets_adapter_when_none(self):
        """Test to_cypher_element gets adapter when none exists."""
        # Reset adapter
        Expr._adapter = None
        
        with patch.object(Expr, 'get_adapter') as mock_get_adapter:
            mock_adapter = Mock()
            mock_element = Mock()
            mock_adapter.to_cypher_element.return_value = mock_element
            mock_get_adapter.return_value = mock_adapter
            
            expr = Expr()
            result = expr.to_cypher_element()
            
            # Should call get_adapter
            mock_get_adapter.assert_called_once()
            # Should use returned adapter
            mock_adapter.to_cypher_element.assert_called_once_with(expr)
            assert result == mock_element


@pytest.mark.unit
class TestExprBaseEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_multiple_expr_instances_share_adapter(self):
        """Test multiple Expr instances share the same class-level adapter."""
        mock_adapter = Mock()
        Expr.set_adapter(mock_adapter)
        
        expr1 = Expr()
        expr2 = Expr()
        
        # Both should use the same adapter
        with patch.object(mock_adapter, 'to_cypher_element') as mock_convert:
            mock_convert.return_value = Mock()
            
            expr1.to_cypher_element()
            expr2.to_cypher_element()
            
            # Should be called twice with different instances
            assert mock_convert.call_count == 2
            assert mock_convert.call_args_list[0][0][0] == expr1
            assert mock_convert.call_args_list[1][0][0] == expr2
    
    def test_adapter_creation_is_lazy(self):
        """Test adapter is only created when first accessed."""
        Expr._adapter = None
        
        with patch('neoalchemy.core.expressions.adapter.ExpressionAdapter') as mock_adapter_class:
            # Just accessing the class shouldn't create adapter
            expr = Expr()
            
            # Should not have called ExpressionAdapter yet
            mock_adapter_class.assert_not_called()
            
            # Now call method that needs adapter
            mock_adapter_class.return_value.to_cypher_element.return_value = Mock()
            expr.to_cypher_element()
            
            # Now should have created adapter
            mock_adapter_class.assert_called_once()
    
    def test_set_adapter_with_none(self):
        """Test set_adapter works with None value."""
        # First set a real adapter
        mock_adapter = Mock()
        Expr.set_adapter(mock_adapter)
        assert Expr._adapter == mock_adapter
        
        # Then set to None
        Expr.set_adapter(None)
        assert Expr._adapter is None
    
    def test_adapter_persistence_across_instances(self):
        """Test adapter setting persists across different instances."""
        mock_adapter = Mock()
        
        # Create first instance and set adapter
        expr1 = Expr()
        Expr.set_adapter(mock_adapter)
        
        # Create second instance
        expr2 = Expr()
        
        # Both should use the same adapter
        assert Expr.get_adapter() == mock_adapter
        
        # Verify through to_cypher_element calls
        mock_adapter.to_cypher_element.return_value = Mock()
        
        expr1.to_cypher_element()
        expr2.to_cypher_element()
        
        # Should have called adapter for both instances
        assert mock_adapter.to_cypher_element.call_count == 2


@pytest.mark.unit
class TestExprBaseImportHandling:
    """Test import handling in the base module."""
    
    def test_type_checking_import_handling(self):
        """Test TYPE_CHECKING block doesn't cause import issues."""
        # This test ensures the TYPE_CHECKING block (line 15) is covered
        from typing import TYPE_CHECKING
        
        # Should be able to import without issues
        assert TYPE_CHECKING is False  # At runtime, TYPE_CHECKING is False
        
        # Re-import the module to ensure TYPE_CHECKING block is executed
        import importlib
        import neoalchemy.core.expressions.base
        
        # Should not raise any import errors
        importlib.reload(neoalchemy.core.expressions.base)
    
    def test_circular_import_avoidance(self):
        """Test that circular imports are avoided in adapter creation."""
        Expr._adapter = None
        
        # This should not cause circular import issues
        with patch('neoalchemy.core.expressions.adapter.ExpressionAdapter') as mock_adapter_class:
            mock_adapter_class.return_value = Mock()
            
            # Should be able to get adapter without circular import
            adapter = Expr.get_adapter()
            
            # Should have successfully created adapter
            mock_adapter_class.assert_called_once()
            assert adapter is not None