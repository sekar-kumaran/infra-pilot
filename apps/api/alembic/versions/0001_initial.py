"""Initial migration — establishes Alembic version tracking in the database.

This migration is intentionally minimal. It proves the Alembic → PostgreSQL
chain works correctly. No domain tables are created in Phase 1.2.

Domain tables (users, roles, alerts, incidents, etc.) will be introduced
in the appropriate feature phases after their models are defined.

Revision: 0001_initial
"""
from typing import Sequence, Union
from alembic import op


# Alembic revision identifiers
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Phase 1.2 initial state.
    No tables are created — this migration establishes the baseline revision.
    Future migrations will build on top of this.
    """
    pass


def downgrade() -> None:
    """Downgrade to pre-migration state (nothing to undo)."""
    pass
