"""
ORM field types for NeoAlchemy.

This module provides specialized field types for Neo4j models.
"""

from typing import Annotated, TypeVar

from pydantic import Field, field_validator

T = TypeVar("T")


class _FieldType:
    """Base class for custom field types that can be used in type annotations."""

    def __init__(self, **field_kwargs):
        self.field_kwargs = field_kwargs

    def __getitem__(self, item):
        """Allow usage like UniqueField[str] in type annotations."""
        # Return an Annotated type with the field
        return Annotated[item, self._make_field()]

    def _make_field(self):
        """Create the actual Field instance - to be overridden by subclasses."""
        raise NotImplementedError


class UniqueFieldType(_FieldType):
    """Type for unique fields that can be used like UniqueField[str]."""

    def __init__(self, *, index: bool = False, **field_kwargs):
        self.index = index
        super().__init__(**field_kwargs)

    def _make_field(self):
        schema_extra = self.field_kwargs.pop("json_schema_extra", {})
        schema_extra.update({"unique": True})
        if self.index:
            schema_extra["index"] = True
        return Field(json_schema_extra=schema_extra, **self.field_kwargs)


class IndexedFieldType(_FieldType):
    """Type for indexed fields that can be used like IndexedField[str]."""

    def _make_field(self):
        schema_extra = self.field_kwargs.pop("json_schema_extra", {})
        schema_extra.update({"index": True})
        return Field(json_schema_extra=schema_extra, **self.field_kwargs)


class PrimaryFieldType(_FieldType):
    """Type for primary key fields that can be used like PrimaryField[str]."""

    def _make_field(self):
        schema_extra = self.field_kwargs.pop("json_schema_extra", {})
        schema_extra.update({"unique": True, "primary": True, "index": True})
        return Field(json_schema_extra=schema_extra, **self.field_kwargs)


# Create instances that can be used in type annotations
UniqueField = UniqueFieldType()
IndexedField = IndexedFieldType()
PrimaryField = PrimaryFieldType()
