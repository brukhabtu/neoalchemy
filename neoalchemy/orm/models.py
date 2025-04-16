"""
Base classes for Neo4j-Pydantic integration.
"""
from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional, Type, TypeVar
from uuid import UUID, uuid4

# Import Neo4j time types
from neo4j.time import DateTime, Date

from pydantic import BaseModel, Field, model_validator

# Import expressions from the expressions module
from neoalchemy.core.expressions import FieldExpr

# Type variable for self-referencing type hints
T = TypeVar("T", bound="Neo4jModel")


class Neo4jModel(BaseModel):
    """Base model with Neo4j compatibility for UUID and datetime serialization."""

    # Common fields for all Neo4j models
    created_at: DateTime = Field(default_factory=lambda: DateTime.from_native(datetime.now()))
    updated_at: Optional[DateTime] = None

    model_config = {
        "arbitrary_types_allowed": True,
        "json_schema_extra": {"example": {"id": "12345678-1234-5678-1234-567812345678"}},
    }

    # Registry for concrete types - override in subclasses
    __registry__: ClassVar[Dict[str, Any]] = {}
    
    # Type identifier attribute name - override in subclasses
    __type_attr__: ClassVar[Optional[str]] = None

    # Class attribute access for field expressions (for type checkers and IDE support)
    @staticmethod
    def __class_getattr__(name: str) -> FieldExpr:
        """Get field expression for class-level attribute access.
        
        This enables Model.name syntax for Python 3.10+ type checkers.
        
        Args:
            name: Attribute name
            
        Returns:
            Field expression
        """
        return FieldExpr(name)

    def model_dump(self, **kwargs):
        """Override to serialize UUIDs as strings."""
        data = super().model_dump(**kwargs)
        # Convert UUIDs to strings
        for key, value in data.items():
            if isinstance(value, UUID):
                data[key] = str(value)
            elif isinstance(value, list):
                data[key] = [str(item) if isinstance(item, UUID) else item for item in value]
        return data
        
    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Override to handle Neo4j specific types like neo4j.time.DateTime and neo4j.time.Date."""
        if isinstance(obj, dict):
            # Create a copy to avoid modifying the original
            obj_copy = obj.copy()
            
            # Convert Neo4j date/time objects to Python equivalents
            for key, value in obj_copy.items():
                # Handle Neo4j DateTime/Date objects
                if hasattr(value, '__class__') and 'neo4j.time' in str(value.__class__):
                    # Try to_native first
                    if hasattr(value, 'to_native'):
                        obj_copy[key] = value.to_native()
                    # Manual conversion as fallback
                    elif hasattr(value, 'year') and hasattr(value, 'month') and hasattr(value, 'day'):
                        # Import here to avoid circular imports
                        from datetime import date, datetime
                        
                        # DateTime (with time components)
                        if hasattr(value, 'hour') and hasattr(value, 'minute') and hasattr(value, 'second'):
                            obj_copy[key] = datetime(
                                value.year, value.month, value.day,
                                value.hour, value.minute, value.second
                            )
                        # Date (date only)
                        else:
                            obj_copy[key] = date(value.year, value.month, value.day)
                
                # Handle lists that might contain Neo4j objects
                elif isinstance(value, list):
                    new_list = []
                    for item in value:
                        if hasattr(item, '__class__') and 'neo4j.time' in str(item.__class__):
                            if hasattr(item, 'to_native'):
                                new_list.append(item.to_native())
                            elif hasattr(item, 'year') and hasattr(item, 'month') and hasattr(item, 'day'):
                                from datetime import date, datetime
                                if hasattr(item, 'hour'):
                                    new_list.append(datetime(
                                        item.year, item.month, item.day,
                                        item.hour, item.minute, item.second
                                    ))
                                else:
                                    new_list.append(date(item.year, item.month, item.day))
                            else:
                                new_list.append(item)
                        else:
                            new_list.append(item)
                    obj_copy[key] = new_list
                    
            return super().model_validate(obj_copy, **kwargs)
        
        return super().model_validate(obj, **kwargs)

    def __init_subclass__(cls, **kwargs):
        """Register subclasses and process array fields."""
        super().__init_subclass__(**kwargs)
        
        # Register array fields based on type annotations
        from neoalchemy.core.field_registration import register_array_field
        
        if hasattr(cls, '__annotations__'):
            for field_name, field_type in cls.__annotations__.items():
                # Check if it's a List type
                origin = getattr(field_type, "__origin__", None)
                if origin is list or origin is List:
                    register_array_field(cls, field_name)

    @model_validator(mode="after")
    def update_timestamps(self):
        """Update timestamps on model changes."""
        self.updated_at = DateTime.from_native(datetime.now())
        return self
    
    @classmethod
    def field(cls, name: str) -> FieldExpr:
        """Get a field expression for the given field name.
        
        Args:
            name: Field name
            
        Returns:
            Field expression for building queries
        """
        return FieldExpr(name)
    
    # Define property accessor for fields
    @classmethod
    def __getitem__(cls, name: str) -> FieldExpr:
        """Allow field access using class['field'] syntax.
        
        Args:
            name: Field name
            
        Returns:
            Field expression
        """
        if name in cls.__annotations__:
            return FieldExpr(name)
        raise KeyError(f"Field {name} not found in {cls.__name__}")
    
    # Static accessors for field expressions via direct class attributes
    @classmethod
    def __getattr__(cls, name: str) -> Any:
        """Enable field expressions through direct class attributes.
        
        This allows clean syntax like:
        - Person.age > 30
        - KNOWS.since > date
        
        Args:
            name: Attribute name
            
        Returns:
            Field expression if attribute is a field, otherwise delegates to parent class
        """
        # Check if it's a field in the current class
        if name in cls.__annotations__:
            # Get array field types for this class
            from neoalchemy.core.field_registration import get_array_fields
            array_field_types = get_array_fields(cls)
            
            field_expr = FieldExpr(name, array_field_types)
            # Cache it on the class for faster access next time
            setattr(cls, name, field_expr)
            return field_expr
            
        # Check if it's a field in any parent class
        for parent in cls.__mro__[1:]:  # Skip the current class
            if hasattr(parent, "__annotations__") and name in parent.__annotations__:
                # Get array field types for the parent class
                from neoalchemy.core.field_registration import get_array_fields
                array_field_types = get_array_fields(parent)
                
                field_expr = FieldExpr(name, array_field_types)
                # Cache it on the class for faster access next time
                setattr(cls, name, field_expr)
                return field_expr
        
        # If we get here, it's not a field, so try regular attribute access
        try:
            return getattr(super(), name)
        except AttributeError:
            # This is what Pydantic does
            raise AttributeError(name)
    
    @classmethod
    def get_registry(cls) -> Dict[str, Any]:
        """Get the registry of entity types.
        
        Returns:
            Dictionary mapping identifiers to entity classes
        """
        return cls.__registry__
    
    @classmethod
    def get_type_value(cls) -> str:
        """Get the type value for this entity.
        
        Returns:
            Type value (class name by default)
        """
        return cls.__name__

    @classmethod
    def get_constraints(cls) -> List[str]:
        """Get all fields with uniqueness constraints.
        
        Returns:
            List of field names with uniqueness constraints
        """
        # Use a class-specific attribute directly on the class
        if not hasattr(cls, '_constraints_cache'):
            # Use list comprehension for cleaner code
            cls._constraints_cache = [
                field_name for field_name, field_info in cls.model_fields.items()
                if field_info.json_schema_extra and field_info.json_schema_extra.get('unique', False)
            ]
        return cls._constraints_cache
    
    @classmethod
    def get_indexes(cls) -> List[str]:
        """Get all fields that should be indexed.
        
        Returns:
            List of field names that should be indexed
        """
        # Use a class-specific attribute directly on the class
        if not hasattr(cls, '_indexes_cache'):
            # Use list comprehension for cleaner code
            cls._indexes_cache = [
                field_name for field_name, field_info in cls.model_fields.items()
                if field_info.json_schema_extra and field_info.json_schema_extra.get('index', False)
            ]
        return cls._indexes_cache


class Node(Neo4jModel):
    """Base class for Neo4j nodes with Pydantic integration."""
    
    # Registry for node types
    __registry__: ClassVar[Dict[str, Type["Node"]]] = {}
    
    # Neo4j label for this node type
    __label__: ClassVar[Optional[str]] = None
    
    def __init_subclass__(cls, **kwargs):
        """Register subclasses in the node registry."""
        super().__init_subclass__(**kwargs)
        
        # Use class name as label if not explicitly set
        if not hasattr(cls, "__label__") or cls.__label__ is None:
            cls.__label__ = cls.__name__
        
        # Register the class if it's not abstract
        if not cls.__name__.startswith("Base") and cls.__name__ != "Node":
            Node.__registry__[cls.__label__] = cls
    
    @classmethod
    def get_label(cls) -> str:
        """Get the Neo4j label for this node type."""
        if cls.__label__ is not None:
            return cls.__label__
        return cls.__name__


class Relationship(Neo4jModel):
    """Base class for Neo4j relationships with Pydantic integration."""
    
    # Registry for relationship types
    __registry__: ClassVar[Dict[str, Type["Relationship"]]] = {}
    
    # Neo4j relationship type
    __type__: ClassVar[Optional[str]] = None
    
    def __init_subclass__(cls, **kwargs):
        """Register subclasses in the relationship registry."""
        super().__init_subclass__(**kwargs)
        
        # Use uppercase class name as type if not explicitly set
        if not hasattr(cls, "__type__") or cls.__type__ is None:
            cls.__type__ = cls.__name__.upper()
        
        # Register the class if it's not abstract
        if not cls.__name__.startswith("Base") and cls.__name__ != "Relationship":
            Relationship.__registry__[cls.__type__] = cls
    
    @classmethod
    def get_type(cls) -> str:
        """Get the Neo4j relationship type."""
        if cls.__type__ is not None:
            return cls.__type__
        return cls.__name__.upper()