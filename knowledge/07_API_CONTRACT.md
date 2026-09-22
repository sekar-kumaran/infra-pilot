# API Contract

## Purpose
Guidelines for building FastAPI REST endpoints.

## Scope
- External and Internal APIs.

## Decisions
- **REST only** for the initial platform. Use versioned routes: `/api/v1/...`
- **Do NOT introduce GraphQL.**
- Return proper HTTP status codes.
- Responses should be standardized JSON models.
- Authentication required by default.
- Error responses must include actionable messages without leaking internal stack traces.

## Interfaces
- OpenAPI specification is the source of truth for the API contract.

## Current Status
- Phase 0: Defined and Locked.
