# Master Architecture

## Purpose
Define the high-level architecture of InfraPilot.

## Scope
- Frontend: Next.js + React.
- Backend API: Python FastAPI modular monolith.
- Async Workers: Celery + RabbitMQ.
- Data Persistence: PostgreSQL.
- Caching/State: Redis.
- Orchestration/Deployment: Docker, Kubernetes, Argo CD.

## Decisions
- Maintain a single modular monolith for API interactions to avoid premature microservices overhead (ADR-002).
- API Style: **REST only**. Use versioned routes (e.g., `/api/v1/...`). Do NOT introduce GraphQL. Do NOT introduce Node.js/Express.
- Message Broker: **RabbitMQ** is authoritative. Celery is the worker framework. Redis is used only for caching, ephemeral state, and rate limiting—NOT as the authoritative task queue. (No Kafka, NATS, Airflow, Temporal).
- Database Responsibilities: **PostgreSQL** stores InfraPilot application state (users, roles, permissions, alerts, incidents, workflow executions, etc.). It is NOT the primary time-series metrics database.
- Observability Responsibilities:
  - **Prometheus**: Metrics collection and time-series querying.
  - **Alertmanager**: Alert routing/grouping.
  - **Nagios**: Traditional host/service checks.
  - **Loki**: Log aggregation.
  - **Grafana**: Visualization.
  - **InfraPilot**: Cross-system operational intelligence (correlation, incident management, diagnosis, policy, automation, audit). InfraPilot orchestrates them; it does not replace them.
- Deployment: Argo CD for GitOps.

## Core Architecture Diagram
```text
                    ┌──────────────────────┐
                    │     Next.js Web UI   │
                    └──────────┬───────────┘
                               │ REST
                               ▼
                    ┌──────────────────────┐
                    │     FastAPI API      │
                    │  Modular Monolith    │
                    └──────────┬───────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
       Event Engine      Incident Engine    Policy Engine
             │                 │                 │
             └─────────────────┼─────────────────┘
                               ▼
                       RabbitMQ + Celery
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
      Automation           Intelligence         Integration
       Workers               Workers              Workers
          │                    │                    │
          ▼                    ▼                    ▼
      Ansible              ML/RCA              Prometheus
      Puppet               Correlation          Nagios
      Terraform            Recommendation       Grafana
      Kubernetes                                 Loki
      Docker
```

## Security & Boundaries
- **API**: No direct infrastructure command execution.
- **Workers**: Perform controlled execution.
- **Integration adapters**: Communicate with external systems.
- **Secrets**: Never stored in source code, never logged, never included in normal API responses.
- **Audit**: Every privileged action must be auditable (actor, action, target, timestamp, request ID, execution ID, outcome).

## Current Status
- Phase 0: Defined and Locked.
