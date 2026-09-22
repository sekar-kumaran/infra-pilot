# ADR-003: PostgreSQL as Application Database

## Status
Accepted

## Context
We need a robust, relational database for configurations, audit logs, and incident states.

## Decision
Use PostgreSQL. It handles JSON well if needed and has strong relational integrity.

## Consequences
- Requires PostgreSQL administration.
- Alembic will be used for schema migrations.
