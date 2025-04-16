"""
Field expression registration system for neoalchemy.

This module provides functionality for registering field expressions
on model classes, allowing for a clean, Pythonic syntax in query expressions.
"""

import venusian  # type: ignore
import importlib
import inspect
from typing import Type, Any, Optional, Dict, Set, List

# Import from correct modules to avoid circular imports
from neoalchemy.core.expressions import FieldExpr

# Create a scanner for Venusian
scanner = venusian.Scanner()

# Registry for models that should have field expressions
_field_registry: Dict[Type, Set[str]] = {}

def register_array_field(model_class: Type, field_name: str) -> None:
    """Register a field as an array field.
    
    This helps the expression system correctly handle array operations.
    
    Args:
        model_class: The model class that has the array field
        field_name: The name of the array field
    """
    if model_class not in _field_registry:
        _field_registry[model_class] = set()
    
    _field_registry[model_class].add(field_name)

def get_array_fields(model_class: Type) -> List[str]:
    """Get the registered array fields for a model class.
    
    Args:
        model_class: The model class to get array fields for
        
    Returns:
        List of field names that are arrays
    """
    return list(_field_registry.get(model_class, set()))

def add_field_expressions(cls: Type[Any]) -> Type[Any]:
    """Add field expressions to a model class.
    
    This decorator creates field expressions for all fields in a model class,
    making them available as class attributes for use in query expressions.
    
    Args:
        cls: The model class to add field expressions to
        
    Returns:
        The class with field expressions added
        
    Example:
        @add_field_expressions
        class CustomModel(BaseModel):
            name: str
            age: int
            
        # Now you can use field expressions in queries:
        query = repo.query(CustomModel).where(CustomModel.age > 30)
    """
    if hasattr(cls, '__annotations__'):
        for field_name in cls.__annotations__:
            if not hasattr(cls, field_name):
                # Check if this is an array field
                array_field_types = get_array_fields(cls)
                field_expr = FieldExpr(field_name, array_field_types)
                
                # Store the field expression on the class
                setattr(cls, field_name, field_expr)
    return cls

def scan_for_models(scanner, name, obj):
    """Callback for Venusian to scan for model classes.
    
    This function is called by Venusian for each object it finds during scanning.
    If the object is a model class, it adds field expressions to it automatically.
    
    Args:
        scanner: The Venusian scanner
        name: The object name
        obj: The object being scanned
    """
    # We can't import Node and Relationship directly due to circular imports,
    # so we check for common attributes that would identify model classes
    if (isinstance(obj, type) and 
            hasattr(obj, '__annotations__') and 
            hasattr(obj, 'model_config')):
        # This is likely a model class
        add_field_expressions(obj)
        
        # Auto-register array fields
        if hasattr(obj, '__annotations__'):
            for field_name, field_type in obj.__annotations__.items():
                # Check if it's a List type
                origin = getattr(field_type, "__origin__", None)
                if origin is list or origin is List:
                    register_array_field(obj, field_name)

def initialize(scan_loaded_classes: bool = True, 
               module_names: Optional[list] = None,
               auto_detect_arrays: bool = True):
    """Initialize the field expression system.
    
    Call this function once at the beginning of your application to set up
    field expressions for your models. This allows you to use the Pythonic
    syntax for field expressions in your queries (e.g., Person.age > 30).
    
    This function:
    1. Optionally processes all already-loaded classes (if scan_loaded_classes is True)
    2. Optionally scans specified modules for models (if module_names is provided)
    3. Automatically detects array fields from type annotations if auto_detect_arrays is True
    
    Args:
        scan_loaded_classes: Whether to add field expressions to all already loaded 
                           model classes. Defaults to True.
        module_names: Optional list of module names to scan for models.
                    If provided, Venusian will scan these modules.
        auto_detect_arrays: Whether to automatically detect array fields from type annotations.
                          Defaults to True.
    
    Example:
        # In your application's initialization code:
        from neoalchemy import initialize
        
        # Initialize existing classes only
        initialize()
        
        # Initialize existing classes and scan specific modules
        initialize(module_names=['myapp.models', 'myapp.custom_models'])
        
        # Only scan specific modules, not existing classes
        initialize(scan_loaded_classes=False, module_names=['myapp.models'])
    """
    # Register the callback with Venusian
    import sys
    for module_name, module in list(sys.modules.items()):
        if module_name.startswith('mcp_megaclaude') and hasattr(module, '__path__'):
            try:
                venusian.attach(module, scan_for_models, category='models')
            except (AttributeError, TypeError):
                pass
    
    # Process already loaded classes if requested
    if scan_loaded_classes:
        # Find all model classes in loaded modules
        for module_name, module in list(sys.modules.items()):
            if not module_name.startswith('_') and module is not None:
                try:
                    for name, obj in inspect.getmembers(module):
                        scan_for_models(scanner, name, obj)
                except (ImportError, AttributeError):
                    pass
    
    # Scan modules for models if requested
    if module_names:
        for module_name in module_names:
            try:
                # Import module if not already imported
                module = importlib.import_module(module_name)
                # Scan the module
                scanner.scan(module, categories=('models',))
            except (ImportError, AttributeError) as e:
                # Log the error rather than failing
                print(f"Warning: Could not scan module {module_name}: {e}")