# Prometheus Integration

## Purpose
Define integration with Prometheus for metrics and alerting.

## Scope
- Ingestion of Prometheus alerts via Alertmanager.
- Querying metrics for incident context.

## Contracts
- Expects standard Alertmanager webhook JSON format.
- Queries use PromQL.

## Constraints
- Read-only queries to Prometheus.
