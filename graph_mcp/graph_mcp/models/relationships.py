"""
Simplified relationships for the engineering management graph.

Core relationship types that express the necessary connections
between Person, Team, Service, Task, and Document entities.
"""

from typing import ClassVar

from neo4j.time import Date
from neoalchemy.orm.models import Relationship


class MEMBER_OF(Relationship):
    """Person is a member of a Team.
    
    Examples:
    - Person member of Team (as engineer, lead, etc.)
    """

    role: str | None = None  # Role in the team (engineer, lead, manager, etc.)
    start_date: Date | None = None  # When membership began
    end_date: Date | None = None  # When membership ended (None if current)

    __type__: ClassVar[str] = "MEMBER_OF"


class RESPONSIBLE_FOR(Relationship):
    """Responsibility relationship.
    
    Examples:
    - Team responsible for Service (as maintainer)
    - Person responsible for Task (as assignee)
    - Person responsible for Document (as author)
    """

    responsibility_type: str | None = None  # Type of responsibility (maintainer, author, assignee, etc.)
    start_date: Date | None = None  # When responsibility began
    end_date: Date | None = None  # When responsibility ended (None if current)

    __type__: ClassVar[str] = "RESPONSIBLE_FOR"


class WORKS_ON(Relationship):
    """Work/contribution relationship.
    
    Examples:
    - Person works on Task
    - Team works on Service
    - Person works on Document
    """

    role: str | None = None  # Role in the work (contributor, reviewer, etc.)
    allocation: float | None = None  # Percentage allocation (0.0 to 1.0)
    start_date: Date | None = None  # When work began
    end_date: Date | None = None  # When work ended (None if ongoing)

    __type__: ClassVar[str] = "WORKS_ON"


class DEPENDS_ON(Relationship):
    """Dependency relationship.
    
    Examples:
    - Task depends on Service
    - Service depends on Service
    - Team depends on Team (for expertise, approval, etc.)
    """

    dependency_type: str | None = None  # Type of dependency (service, expertise, approval, etc.)
    criticality: str | None = None  # Criticality level (critical, high, medium, low)

    __type__: ClassVar[str] = "DEPENDS_ON"


class REFERENCES(Relationship):
    """Reference/mention relationship.
    
    Examples:
    - Document references Task (discusses, tracks)
    - Document references Service (documents)
    - Task references Service (impacts, uses)
    """

    reference_type: str | None = None  # Type of reference (documents, discusses, mentions, tracks, etc.)
    context: str | None = None  # Additional context about the reference

    __type__: ClassVar[str] = "REFERENCES"