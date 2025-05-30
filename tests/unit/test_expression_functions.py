"""
Unit tests for expression function classes.

These tests focus on FunctionExpr and FunctionComparisonExpr classes in isolation.
"""

import pytest
from unittest.mock import Mock, patch

from neoalchemy.core.expressions.functions import FunctionExpr, FunctionComparisonExpr


@pytest.mark.unit
class TestFunctionExpr:
    """Test FunctionExpr class in isolation."""

    def test_function_expr_construction(self):
        """Test FunctionExpr constructor sets fields correctly."""
        args = ["field1", "field2"]
        expr = FunctionExpr("length", args)
        
        assert expr.func_name == "length"
        assert expr.args == args

    def test_function_expr_with_empty_args(self):
        """Test FunctionExpr constructor with empty args."""
        expr = FunctionExpr("count", [])
        
        assert expr.func_name == "count"
        assert expr.args == []

    def test_function_expr_with_single_arg(self):
        """Test FunctionExpr constructor with single argument."""
        expr = FunctionExpr("upper", ["name"])
        
        assert expr.func_name == "upper"
        assert expr.args == ["name"]

    @patch('neoalchemy.core.expressions.operators.OperatorExpr')
    def test_eq_creates_function_comparison_expr(self, mock_operator):
        """Test __eq__ creates FunctionComparisonExpr."""
        func_expr = FunctionExpr("length", ["name"])
        
        with patch('neoalchemy.core.expressions.functions.FunctionComparisonExpr') as mock_func_comp:
            result = func_expr.__eq__(5)
            
            mock_func_comp.assert_called_once_with(func_expr, "=", 5)
            assert result == mock_func_comp.return_value

    @patch('neoalchemy.core.expressions.operators.OperatorExpr')
    def test_ne_creates_function_comparison_expr(self, mock_operator):
        """Test __ne__ creates FunctionComparisonExpr."""
        func_expr = FunctionExpr("length", ["name"])
        
        with patch('neoalchemy.core.expressions.functions.FunctionComparisonExpr') as mock_func_comp:
            result = func_expr.__ne__(5)
            
            mock_func_comp.assert_called_once_with(func_expr, "<>", 5)
            assert result == mock_func_comp.return_value

    @patch('neoalchemy.core.expressions.operators.OperatorExpr')
    def test_gt_creates_function_comparison_expr(self, mock_operator):
        """Test __gt__ creates FunctionComparisonExpr."""
        func_expr = FunctionExpr("length", ["name"])
        
        with patch('neoalchemy.core.expressions.functions.FunctionComparisonExpr') as mock_func_comp:
            result = func_expr.__gt__(5)
            
            mock_func_comp.assert_called_once_with(func_expr, ">", 5)
            assert result == mock_func_comp.return_value

    @patch('neoalchemy.core.expressions.operators.OperatorExpr')
    def test_lt_creates_function_comparison_expr(self, mock_operator):
        """Test __lt__ creates FunctionComparisonExpr."""
        func_expr = FunctionExpr("length", ["name"])
        
        with patch('neoalchemy.core.expressions.functions.FunctionComparisonExpr') as mock_func_comp:
            result = func_expr.__lt__(5)
            
            mock_func_comp.assert_called_once_with(func_expr, "<", 5)
            assert result == mock_func_comp.return_value

    @patch('neoalchemy.core.expressions.operators.OperatorExpr')
    def test_ge_creates_function_comparison_expr(self, mock_operator):
        """Test __ge__ creates FunctionComparisonExpr."""
        func_expr = FunctionExpr("length", ["name"])
        
        with patch('neoalchemy.core.expressions.functions.FunctionComparisonExpr') as mock_func_comp:
            result = func_expr.__ge__(5)
            
            mock_func_comp.assert_called_once_with(func_expr, ">=", 5)
            assert result == mock_func_comp.return_value

    @patch('neoalchemy.core.expressions.operators.OperatorExpr')
    def test_le_creates_function_comparison_expr(self, mock_operator):
        """Test __le__ creates FunctionComparisonExpr."""
        func_expr = FunctionExpr("length", ["name"])
        
        with patch('neoalchemy.core.expressions.functions.FunctionComparisonExpr') as mock_func_comp:
            result = func_expr.__le__(5)
            
            mock_func_comp.assert_called_once_with(func_expr, "<=", 5)
            assert result == mock_func_comp.return_value


@pytest.mark.unit
class TestFunctionComparisonExpr:
    """Test FunctionComparisonExpr class in isolation."""

    def test_function_comparison_expr_construction(self):
        """Test FunctionComparisonExpr constructor sets fields correctly."""
        func_expr = Mock()
        comparison = FunctionComparisonExpr(func_expr, ">", 10)
        
        assert comparison.func_expr is func_expr
        assert comparison.operator == ">"
        assert comparison.value == 10

    def test_function_comparison_expr_with_different_operators(self):
        """Test FunctionComparisonExpr with different comparison operators."""
        func_expr = Mock()
        
        # Test various operators
        operators = ["=", "<>", ">", "<", ">=", "<="]
        for op in operators:
            comparison = FunctionComparisonExpr(func_expr, op, 5)
            assert comparison.operator == op
            assert comparison.func_expr is func_expr
            assert comparison.value == 5

    def test_function_comparison_expr_with_different_value_types(self):
        """Test FunctionComparisonExpr with different value types."""
        func_expr = Mock()
        
        # String value
        comp1 = FunctionComparisonExpr(func_expr, "=", "test")
        assert comp1.value == "test"
        
        # Integer value
        comp2 = FunctionComparisonExpr(func_expr, ">", 42)
        assert comp2.value == 42
        
        # Float value
        comp3 = FunctionComparisonExpr(func_expr, "<=", 3.14)
        assert comp3.value == 3.14
        
        # None value
        comp4 = FunctionComparisonExpr(func_expr, "IS NULL", None)
        assert comp4.value is None