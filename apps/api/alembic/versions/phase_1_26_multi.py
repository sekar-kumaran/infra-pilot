"""Phase 1-26 Multi-Tenant Schema Foundation with Defensive Table Inspection

Revision ID: phase_1_26_multi
Revises: None
Create Date: 2026-11-17 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "phase_1_26_multi"
down_revision = None
branch_labels = None
depends_on = None

TENANT_SCOPED_TABLES = [
    "users",
    "applications",
    "environments",
    "infrastructure_resources",
    "integrations",
    "raw_events",
    "alerts",
    "incidents",
    "playbooks",
    "automation_executions",
    "policies",
    "audit_events",
    "operation_workflows",
]

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "tenants" not in existing_tables:
        op.create_table(
            "tenants",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False, unique=True),
            sa.Column("slug", sa.String(length=128), nullable=False, unique=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        existing_tables.add("tenants")

    # Defensively inspect existing tables and columns before altering
    for table in TENANT_SCOPED_TABLES:
        if table in existing_tables:
            existing_cols = {c["name"] for c in inspector.get_columns(table)}
            if "tenant_id" not in existing_cols:
                op.add_column(table, sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
                op.create_index(op.f(f"ix_{table}_tenant_id"), table, ["tenant_id"], unique=False)
                op.create_foreign_key(
                    f"fk_{table}_tenant_id",
                    table,
                    "tenants",
                    ["tenant_id"],
                    ["id"],
                    ondelete="CASCADE",
                )

def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    for table in reversed(TENANT_SCOPED_TABLES):
        if table in existing_tables:
            existing_cols = {c["name"] for c in inspector.get_columns(table)}
            if "tenant_id" in existing_cols:
                op.drop_constraint(f"fk_{table}_tenant_id", table, type_="foreignkey")
                op.drop_index(op.f(f"ix_{table}_tenant_id"), table_name=table)
                op.drop_column(table, "tenant_id")
