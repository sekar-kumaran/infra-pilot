# Observability Contract

## Purpose
How InfraPilot itself is monitored.

## Scope
- App metrics, structured logging.

## Decisions
- Expose `/metrics` for Prometheus.
- Use structured JSON logging for Loki ingestion.
- Always include `execution_id` or `trace_id` in logs.

## Current Status
- Phase 0.
