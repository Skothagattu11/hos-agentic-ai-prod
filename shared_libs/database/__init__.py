"""
Database utilities for HolisticOS MVP
Provides connection pooling and database management functionality
"""

from .connection_pool import DatabasePool, db_pool

__all__ = ['DatabasePool', 'db_pool']