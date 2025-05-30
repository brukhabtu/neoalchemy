"""Shared test models for integration tests."""
from pydantic import Field
from neoalchemy.orm.models import Node, Relationship
from neoalchemy.orm.fields import PrimaryField


class Person(Node):
    """Shared person model for tests."""
    __label__ = "Person"
    
    id: str = Field(default="")
    name: str
    age: int
    email: PrimaryField[str] = Field(default="")  # Primary key automatically unique
    tags: list[str] = Field(default_factory=list)
    active: bool = Field(default=True)


class Company(Node):
    """Shared company model for tests."""
    __label__ = "Company"
    
    id: str = Field(default="")
    name: PrimaryField[str] = Field()  # Primary key (automatically indexed)
    founded: int
    revenue: float = Field(default=0.0)
    industry: str = Field(default="")


class Product(Node):
    """Shared product model for tests."""
    __label__ = "Product"
    
    sku: str = Field(..., json_schema_extra={"unique": True})
    name: str = Field(..., json_schema_extra={"index": True})
    price: float
    category: str = Field(default="")


class User(Node):
    """Shared user model for tests."""
    __label__ = "User"
    
    email: str = Field(..., json_schema_extra={"unique": True})
    username: str = Field(..., json_schema_extra={"unique": True, "index": True})
    age: int = Field(..., json_schema_extra={"index": True})
    account_number: str = Field(default="", min_length=10, max_length=10, json_schema_extra={"unique": True})
    balance: float = Field(default=0.0, ge=0.0)
    status: str = Field(default="active", pattern="^(active|inactive|suspended)$")


class WorksAt(Relationship):
    """Shared employment relationship for tests."""
    __type__ = "WORKS_AT"
    
    position: str
    since: int
    department: str = Field(default="")
    employee_id: str = Field(default="", json_schema_extra={"unique": True})