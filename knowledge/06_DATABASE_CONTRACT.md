# Database Contract

## Purpose
Define interaction rules for PostgreSQL.

## Scope
- SQLAlchemy models, Alembic migrations.

## Decisions
- All schema changes require an Alembic migration.
- Use declarative base.
- Do not bypass the ORM unless for heavily optimized queries.
- Include audit fields (`created_at`, `updated_at`, `deleted_at`) for soft deletes where applicable.

## Current Status
- Phase 0.
