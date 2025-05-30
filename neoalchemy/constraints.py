"""
Constraint management for NeoAlchemy models.

This module re-exports constraint functionality from the ORM module
for backward compatibility. The actual implementation is in neoalchemy.orm.constraints.
"""

# Re-export constraint functions from ORM module for backward compatibility
from neoalchemy.orm.constraints import setup_constraints

__all__ = ["setup_constraints"]