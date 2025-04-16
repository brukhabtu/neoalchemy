"""
Test models for NeoAlchemy tests.

This module defines all the test models used across different test files.
"""

from datetime import datetime

from neoalchemy.orm.models import Node, Relationship
from pydantic import Field

from neoalchemy import initialize


class Person(Node):
    """Person test model."""
    name: str
    age: int
    email: str = ""
    active: bool = True
    score: float = 0.0
    tags: list[str] = []


class Company(Node):
    """Company test model."""
    name: str
    founded: int
    industry: str = ""
    revenue: float = 0.0
    active: bool = True


class Product(Node):
    """Product test model."""
    name: str
    price: float
    category: str
    in_stock: bool = True


class WORKS_FOR(Relationship):
    """Employment relationship model."""
    role: str
    since: datetime = Field(default_factory=datetime.now)


class PRODUCES(Relationship):
    """Production relationship model."""
    since_year: int


# Remove automatic initialization to let tests handle it properly
# initialize()