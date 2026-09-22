# ADR-001: Monorepo Architecture

## Status
Accepted

## Context
InfraPilot consists of a frontend, backend, workers, and multiple integrations. Keeping these in separate repositories increases cognitive load and slows down atomic changes.

## Decision
We will use a monorepo structure.

## Consequences
- Easier coordination of full-stack features.
- CI/CD must be configured to selectively build only changed applications.
