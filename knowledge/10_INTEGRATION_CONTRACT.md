# Integration Contract

## Purpose
Guidelines for adding new third-party integrations and defining the Canonical Provider Adapter Model.

## Canonical Provider Adapter Model
Every monitoring provider must implement conceptually:
```text
Provider Payload
      ↓
Provider Adapter
      ↓
RawEvent
      ↓
Normalizer
      ↓
Canonical Alert
```

The core incident engine must NEVER contain provider-specific logic (e.g., `if provider == "nagios"`). Provider-specific logic belongs inside provider adapters.

## Contracts
Define interfaces for:
- `AlertProvider`
- `MetricsProvider`
- `LogsProvider`
- `AutomationProvider`
- `ProvisioningProvider`

All integrations must implement a common interface/protocol for alert normalization. Failures to connect must not crash the main application.

## Current Status
- Phase 0: Defined and Locked.
- Phase 1.6: Framework Implemented (AdapterRegistry, IntegrationService, TestProviderAdapter, Celery integration)
