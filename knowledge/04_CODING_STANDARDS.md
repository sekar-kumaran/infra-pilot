# Coding Standards

## Purpose
Ensure consistency across the Python and TypeScript codebases.

## Scope
- Frontend (TS/React)
- Backend (Python/FastAPI)

## Decisions
- Backend: Use `black` and `ruff` for formatting and linting. Type hints are mandatory (`mypy`).
- Frontend: Use `prettier` and `eslint`. Strict TypeScript mode enabled.
- All code must follow the principles in `03_ENGINEERING_RULES.md`.

## Examples
- Use Pydantic for all data validation in FastAPI endpoints.
- Separate business logic from routing.

## Current Status
- Standards defined. CI enforcement to be implemented in Phase 8.
