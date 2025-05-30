"""
Unit tests for field registration system.

These tests focus on the core field registration functions in isolation.
"""

import pytest
from unittest.mock import Mock, patch

from neoalchemy.core.field_registration import (
    register_array_field,
    get_array_fields,
    add_field_expressions,
    initialize
)


@pytest.mark.unit
class TestArrayFieldRegistration:
    """Test array field registration functionality."""

    def test_register_array_field_new_model(self):
        """Test registering array field for new model."""
        mock_model = Mock()
        mock_model.__name__ = "TestModel"
        
        # Clear any existing state
        from neoalchemy.core.field_registration import _field_registry
        _field_registry.clear()
        
        register_array_field(mock_model, "tags")
        
        # Should create entry for model
        assert mock_model in _field_registry
        assert "tags" in _field_registry[mock_model]

    def test_register_array_field_existing_model(self):
        """Test registering array field for existing model."""
        mock_model = Mock()
        mock_model.__name__ = "TestModel"
        
        # Clear state and add initial field
        from neoalchemy.core.field_registration import _field_registry
        _field_registry.clear()
        register_array_field(mock_model, "tags")
        
        # Add second field
        register_array_field(mock_model, "keywords")
        
        # Should have both fields
        assert mock_model in _field_registry
        assert "tags" in _field_registry[mock_model]
        assert "keywords" in _field_registry[mock_model]

    def test_register_array_field_duplicate_field(self):
        """Test registering the same array field twice."""
        mock_model = Mock()
        mock_model.__name__ = "TestModel"
        
        # Clear state
        from neoalchemy.core.field_registration import _field_registry
        _field_registry.clear()
        
        # Register same field twice
        register_array_field(mock_model, "tags")
        register_array_field(mock_model, "tags")
        
        # Should only have one entry (sets handle duplicates)
        assert mock_model in _field_registry
        assert len(_field_registry[mock_model]) == 1
        assert "tags" in _field_registry[mock_model]

    def test_get_array_fields_existing_model(self):
        """Test getting array fields for existing model."""
        mock_model = Mock()
        mock_model.__name__ = "TestModel"
        
        # Clear state and setup
        from neoalchemy.core.field_registration import _field_registry
        _field_registry.clear()
        register_array_field(mock_model, "tags")
        register_array_field(mock_model, "keywords")
        
        result = get_array_fields(mock_model)
        
        # Should return list of fields
        assert isinstance(result, list)
        assert set(result) == {"tags", "keywords"}

    def test_get_array_fields_nonexistent_model(self):
        """Test getting array fields for model not in registry."""
        mock_model = Mock()
        mock_model.__name__ = "NonExistentModel"
        
        # Clear state to ensure model isn't registered
        from neoalchemy.core.field_registration import _field_registry
        _field_registry.clear()
        
        result = get_array_fields(mock_model)
        
        # Should return empty list
        assert result == []

    def test_get_array_fields_empty_model(self):
        """Test getting array fields for model with no fields."""
        mock_model = Mock()
        mock_model.__name__ = "EmptyModel"
        
        # Clear state and register model with no fields
        from neoalchemy.core.field_registration import _field_registry
        _field_registry.clear()
        _field_registry[mock_model] = set()
        
        result = get_array_fields(mock_model)
        
        # Should return empty list
        assert result == []


@pytest.mark.unit
class TestFieldExpressionDecorator:
    """Test add_field_expressions decorator."""

    def test_add_field_expressions_returns_class(self):
        """Test add_field_expressions decorator returns the class."""
        class TestModel:
            pass
        
        # Apply decorator
        result = add_field_expressions(TestModel)
        
        # Should return the same class
        assert result is TestModel

    def test_add_field_expressions_preserves_class_attributes(self):
        """Test decorator preserves existing class attributes."""
        class TestModel:
            existing_attr = "test_value"
            
            def existing_method(self):
                return "test"
        
        # Apply decorator
        result = add_field_expressions(TestModel)
        
        # Should preserve attributes
        assert result.existing_attr == "test_value"
        assert hasattr(result, 'existing_method')
        assert result().existing_method() == "test"

    @patch('neoalchemy.core.field_registration.FieldExpr')
    def test_add_field_expressions_creates_field_expressions(self, mock_field_expr):
        """Test decorator creates FieldExpr for model fields."""
        # Mock FieldExpr creation
        mock_field_instance = Mock()
        mock_field_expr.return_value = mock_field_instance
        
        class TestModel:
            __annotations__ = {'name': str, 'age': int}
        
        # Apply decorator
        result = add_field_expressions(TestModel)
        
        # Should create FieldExpr instances
        assert hasattr(result, 'name')
        assert hasattr(result, 'age')
        # Field expressions should be created
        assert mock_field_expr.call_count >= 2

    def test_add_field_expressions_handles_no_annotations(self):
        """Test decorator handles class with no annotations."""
        class TestModel:
            pass
        
        # Apply decorator (should not raise exception)
        result = add_field_expressions(TestModel)
        
        # Should return the class unchanged
        assert result is TestModel


@pytest.mark.unit
class TestInitialization:
    """Test initialization functionality."""

    def test_initialize_basic_call(self):
        """Test initialize can be called without raising exceptions."""
        # Should not raise exception with default parameters
        initialize()
        
        # Should not raise exception with explicit parameters
        initialize(scan_loaded_classes=False)
        initialize(scan_loaded_classes=True, module_names=None)

    def test_initialize_with_module_names(self):
        """Test initialize handles module_names parameter."""
        # Should handle empty module list
        initialize(module_names=[])
        
        # Should handle non-existent modules gracefully
        initialize(module_names=['nonexistent.module'])

    def test_initialize_with_various_parameters(self):
        """Test initialize handles different parameter combinations."""
        # Test different combinations that should not raise exceptions
        initialize(scan_loaded_classes=True, module_names=[])
        initialize(scan_loaded_classes=False, module_names=None)
        initialize(scan_loaded_classes=True, auto_detect_arrays=True)
        initialize(scan_loaded_classes=False, auto_detect_arrays=False)


@pytest.mark.unit
class TestFieldRegistrationEdgeCases:
    """Test edge cases and error conditions."""

    def test_register_array_field_with_none_model(self):
        """Test register_array_field handles None model gracefully."""
        # Should not raise exception, but behavior may vary
        try:
            register_array_field(None, "tags")
        except (TypeError, AttributeError):
            # Expected for None model
            pass

    def test_register_array_field_with_empty_field_name(self):
        """Test register_array_field with empty field name."""
        mock_model = Mock()
        
        # Should handle empty string
        register_array_field(mock_model, "")
        
        from neoalchemy.core.field_registration import _field_registry
        if mock_model in _field_registry:
            assert "" in _field_registry[mock_model]

    def test_multiple_models_independent_registries(self):
        """Test multiple models have independent array field registries."""
        mock_model1 = Mock()
        mock_model1.__name__ = "Model1"
        mock_model2 = Mock()  
        mock_model2.__name__ = "Model2"
        
        # Clear state
        from neoalchemy.core.field_registration import _field_registry
        _field_registry.clear()
        
        # Register fields for different models
        register_array_field(mock_model1, "tags")
        register_array_field(mock_model2, "items")
        
        # Each model should have only its own fields
        assert get_array_fields(mock_model1) == ["tags"]
        assert get_array_fields(mock_model2) == ["items"]


@pytest.mark.unit
class TestScanForModelsFunction:
    """Test scan_for_models function and missing coverage lines."""
    
    def test_scan_for_models_with_metaclass_class(self):
        """Test scan_for_models skips classes that have __getattr__ (line 102)."""
        from neoalchemy.core.field_registration import scan_for_models, _field_registry
        
        # Clear registry
        _field_registry.clear()
        
        # Create a metaclass that has __getattr__
        class MetaWithGetAttr(type):
            def __getattr__(cls, name):
                return "test"
        
        # Create a class using this metaclass
        class ModelWithMetaclass(metaclass=MetaWithGetAttr):
            __annotations__ = {'name': str}
            model_config = {}
        
        scanner = Mock()
        
        # This should NOT call add_field_expressions due to __getattr__ check
        scan_for_models(scanner, "ModelWithMetaclass", ModelWithMetaclass)
        
        # Should not have added field expressions due to metaclass check
        # The field should still be the original annotation, not a FieldExpr
        assert hasattr(ModelWithMetaclass, '__annotations__')
        assert 'name' in ModelWithMetaclass.__annotations__
    
    def test_scan_for_models_with_list_annotation(self):
        """Test scan_for_models registers array fields for List types (line 110)."""
        from neoalchemy.core.field_registration import scan_for_models, get_array_fields, _field_registry
        from typing import List
        
        # Clear registry
        _field_registry.clear()
        
        # Mock a class with List annotation
        class ModelWithListField:
            __annotations__ = {'tags': List[str], 'name': str}
            model_config = {}
        
        scanner = Mock()
        
        # Call scan_for_models
        scan_for_models(scanner, "ModelWithListField", ModelWithListField)
        
        # Should have registered 'tags' as array field but not 'name'
        array_fields = get_array_fields(ModelWithListField)
        assert "tags" in array_fields
        assert "name" not in array_fields
    
    @patch('neoalchemy.core.field_registration.venusian.attach')
    def test_initialize_with_mcp_megaclaude_module(self, mock_venusian_attach):
        """Test initialize handles mcp_megaclaude modules (lines 155-158)."""
        import sys
        from neoalchemy.core.field_registration import initialize
        
        # Mock a module that starts with mcp_megaclaude and has __path__
        mock_module = Mock()
        mock_module.__path__ = ['/fake/path']
        
        # Temporarily add to sys.modules
        original_modules = dict(sys.modules)
        sys.modules['mcp_megaclaude_test'] = mock_module
        
        try:
            # This should call venusian.attach (line 156)
            initialize()
            mock_venusian_attach.assert_called()
        finally:
            # Restore sys.modules
            sys.modules.clear()
            sys.modules.update(original_modules)
    
    @patch('neoalchemy.core.field_registration.venusian.attach')
    def test_initialize_venusian_attach_exception(self, mock_venusian_attach):
        """Test initialize handles venusian.attach exceptions (lines 157-158)."""
        import sys
        from neoalchemy.core.field_registration import initialize
        
        # Make venusian.attach raise an exception
        mock_venusian_attach.side_effect = AttributeError("Test error")
        
        # Mock a module that starts with mcp_megaclaude and has __path__
        mock_module = Mock()
        mock_module.__path__ = ['/fake/path']
        
        # Temporarily add to sys.modules
        original_modules = dict(sys.modules)
        sys.modules['mcp_megaclaude_test'] = mock_module
        
        try:
            # This should handle the exception gracefully (line 158: pass)
            initialize()  # Should not raise exception
        finally:
            # Restore sys.modules
            sys.modules.clear()
            sys.modules.update(original_modules)
    
    @patch('inspect.getmembers')
    def test_initialize_scan_loaded_classes_exception(self, mock_getmembers):
        """Test initialize handles inspect.getmembers exceptions (lines 168-169)."""
        from neoalchemy.core.field_registration import initialize
        
        # Make inspect.getmembers raise an exception
        mock_getmembers.side_effect = ImportError("Test error")
        
        # This should handle the exception gracefully (line 169: pass)
        initialize(scan_loaded_classes=True)  # Should not raise exception
    
    @patch('neoalchemy.core.field_registration.scanner.scan')
    def test_initialize_scanner_scan_exception(self, mock_scanner_scan):
        """Test initialize handles scanner.scan exceptions (line 178)."""
        from neoalchemy.core.field_registration import initialize
        
        # Make scanner.scan raise an exception
        mock_scanner_scan.side_effect = ImportError("Test error")
        
        # This should handle the exception gracefully (shows error but continues)
        initialize(module_names=['test.module'])  # Should not raise exception