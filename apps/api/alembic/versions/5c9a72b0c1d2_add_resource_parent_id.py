"""add_resource_parent_id

Revision ID: 5c9a72b0c1d2
Revises: 106dc4736f4d
Create Date: 2026-09-23 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c9a72b0c1d2'
down_revision: Union[str, Sequence[str], None] = ('106dc4736f4d', '3fa06386bab1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add parent_id to infrastructure_resources
    op.add_column('infrastructure_resources', sa.Column('parent_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_infrastructure_resources_parent_id',
        'infrastructure_resources',
        'infrastructure_resources',
        ['parent_id'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_infrastructure_resources_parent_id', 'infrastructure_resources', ['parent_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_infrastructure_resources_parent_id', table_name='infrastructure_resources')
    op.drop_constraint('fk_infrastructure_resources_parent_id', 'infrastructure_resources', type_='foreignkey')
    op.drop_column('infrastructure_resources', 'parent_id')
