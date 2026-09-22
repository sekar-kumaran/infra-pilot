# Alertmanager Integration

## Purpose
Define ingestion of alerts.

## Scope
- API endpoint to receive webhook POSTs from Alertmanager.

## Contracts
- Validate incoming payload structure.
- Map labels and annotations to normalized InfraPilot Incident/Alert schema.
