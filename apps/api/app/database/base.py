"""
SQLAlchemy declarative base.

All domain models must inherit from Base.
This module imports Base — future model modules will import and subclass it,
which causes their tables to register with Base.metadata automatically.
Alembic's env.py uses Base.metadata for autogenerate support.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Application-wide SQLAlchemy declarative base."""
    pass
