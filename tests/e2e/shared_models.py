"""Shared model definitions for E2E tests.

These models represent realistic business entities for comprehensive workflow testing.
"""
from typing import Optional, List
from neoalchemy.orm.models import Node, Relationship
from neoalchemy.orm.fields import PrimaryField, UniqueField, IndexedField


class Person(Node):
    """Person entity for realistic business scenarios."""
    email: PrimaryField[str]
    name: IndexedField[str]
    age: int
    active: bool = True
    tags: List[str] = []
    score: float = 0.0
    department: Optional[str] = None
    hire_date: Optional[str] = None
    
    
class Company(Node):
    """Company entity for business relationship modeling."""
    name: PrimaryField[str]
    founded: int
    industry: IndexedField[str] = ""
    employee_count: int = 0
    revenue: float = 0.0
    headquarters: Optional[str] = None


class Product(Node):
    """Product entity for e-commerce and inventory scenarios."""
    sku: PrimaryField[str]  # SKU is naturally the primary identifier for products
    name: IndexedField[str]
    price: IndexedField[float]
    category: IndexedField[str] = ""
    description: Optional[str] = None
    in_stock: bool = True
    manufacturer: Optional[str] = None


class Project(Node):
    """Project entity for workflow and collaboration scenarios."""
    code: PrimaryField[str]
    name: IndexedField[str]
    status: IndexedField[str] = "active"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    budget: float = 0.0
    priority: int = 1


class Department(Node):
    """Department entity for organizational hierarchy."""
    name: PrimaryField[str]
    budget: float = 0.0
    head_count: int = 0
    location: Optional[str] = None


# Relationships

class WorksAt(Relationship):
    """Employment relationship with comprehensive attributes."""
    role: str
    since: int
    salary: float = 0.0
    employment_type: str = "full-time"
    performance_rating: float = 0.0


class WorksOn(Relationship):
    """Project assignment relationship."""
    role: str
    allocation: float = 1.0  # percentage of time
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class Uses(Relationship):
    """Product usage relationship."""
    since: int
    frequency: str = "daily"
    license_type: str = "standard"
    last_used: Optional[str] = None


class PartOf(Relationship):
    """Hierarchical relationship for departments."""
    since: int
    responsibility: Optional[str] = None


class ManufacturedBy(Relationship):
    """Product manufacturing relationship."""
    since: int
    contract_type: str = "standard"
    quality_rating: float = 0.0


class Collaborates(Relationship):
    """Inter-company collaboration."""
    since: int
    contract_value: float = 0.0
    project_count: int = 0


class Reports(Relationship):
    """Management hierarchy relationship."""
    since: int
    review_cycle: str = "quarterly"
    direct_report: bool = True


class Manages(Relationship):
    """Department management relationship."""
    since: int
    budget_authority: float = 0.0
    team_size: int = 0