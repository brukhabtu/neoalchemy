"""
Unit tests for expression system components.

These tests focus on individual expression classes in isolation,
testing their behavior without dependencies on other components.
"""

import pytest
from unittest.mock import Mock, patch

from neoalchemy.core.expressions.operators import OperatorExpr, CompositeExpr, NotExpr
from neoalchemy.core.expressions.logical import LogicalExpr


@pytest.mark.unit
class TestOperatorExpr:
    """Test OperatorExpr class in isolation."""

    def test_operator_expr_construction(self):
        """Test OperatorExpr constructor sets fields correctly."""
        expr = OperatorExpr("name", "=", "Alice")
        
        assert expr.field == "name"
        assert expr.operator == "="
        assert expr.value == "Alice"

    def test_operator_expr_construction_with_different_types(self):
        """Test OperatorExpr works with different value types."""
        # String value
        expr1 = OperatorExpr("name", "=", "Alice")
        assert expr1.value == "Alice"
        
        # Integer value
        expr2 = OperatorExpr("age", ">", 30)
        assert expr2.value == 30
        
        # Boolean value
        expr3 = OperatorExpr("active", "=", True)
        assert expr3.value is True
        
        # None value
        expr4 = OperatorExpr("email", "IS NULL", None)
        assert expr4.value is None


@pytest.mark.unit
class TestCompositeExpr:
    """Test CompositeExpr class in isolation."""

    def test_composite_expr_construction(self):
        """Test CompositeExpr constructor sets fields correctly."""
        left = Mock()
        right = Mock()
        
        expr = CompositeExpr(left, "AND", right)
        
        assert expr.left is left
        assert expr.op == "AND"
        assert expr.right is right

    def test_composite_expr_with_or_operator(self):
        """Test CompositeExpr constructor with OR operator."""
        left = Mock()
        right = Mock()
        
        expr = CompositeExpr(left, "OR", right)
        
        assert expr.left is left
        assert expr.op == "OR"
        assert expr.right is right


@pytest.mark.unit
class TestNotExpr:
    """Test NotExpr class in isolation."""

    def test_not_expr_construction(self):
        """Test NotExpr constructor sets field correctly."""
        inner_expr = Mock()
        
        expr = NotExpr(inner_expr)
        
        assert expr.expr is inner_expr


@pytest.mark.unit
class TestLogicalExpr:
    """Test LogicalExpr logical operator methods."""

    def test_logical_expr_and_creates_composite(self):
        """Test that __and__ method creates CompositeExpr with correct args."""
        left_expr = LogicalExpr()
        right_expr = Mock()
        
        with patch('neoalchemy.core.expressions.operators.CompositeExpr') as mock_composite:
            result = left_expr.__and__(right_expr)
            
            mock_composite.assert_called_once_with(left_expr, "AND", right_expr)
            assert result == mock_composite.return_value

    def test_logical_expr_or_creates_composite(self):
        """Test that __or__ method creates CompositeExpr with correct args."""
        left_expr = LogicalExpr()
        right_expr = Mock()
        
        with patch('neoalchemy.core.expressions.operators.CompositeExpr') as mock_composite:
            result = left_expr.__or__(right_expr)
            
            mock_composite.assert_called_once_with(left_expr, "OR", right_expr)
            assert result == mock_composite.return_value

    def test_logical_expr_invert_creates_not_expr(self):
        """Test that __invert__ method creates NotExpr with correct args."""
        expr = LogicalExpr()
        
        with patch('neoalchemy.core.expressions.operators.NotExpr') as mock_not:
            result = expr.__invert__()
            
            mock_not.assert_called_once_with(expr)
            assert result == mock_not.return_value

    def test_logical_expr_bitwise_operators_create_expressions(self):
        """Test that bitwise operators create the correct expression types."""
        left_expr = LogicalExpr()
        right_expr = LogicalExpr()
        
        # Test & operator creates CompositeExpr via __and__
        with patch('neoalchemy.core.expressions.operators.CompositeExpr') as mock_composite:
            result = left_expr & right_expr
            mock_composite.assert_called_once_with(left_expr, "AND", right_expr)
        
        # Test | operator creates CompositeExpr via __or__
        with patch('neoalchemy.core.expressions.operators.CompositeExpr') as mock_composite:
            result = left_expr | right_expr
            mock_composite.assert_called_once_with(left_expr, "OR", right_expr)
        
        # Test ~ operator creates NotExpr via __invert__
        with patch('neoalchemy.core.expressions.operators.NotExpr') as mock_not:
            result = ~left_expr
            mock_not.assert_called_once_with(left_expr)