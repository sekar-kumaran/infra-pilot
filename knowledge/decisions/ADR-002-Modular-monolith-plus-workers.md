# ADR-002: Modular Monolith Plus Workers

## Status
Accepted

## Context
Microservices introduce immense operational overhead. InfraPilot is an operational tool, so making it complex to run defeats the purpose. However, we need scalable, isolated task execution.

## Decision
Build the API as a FastAPI modular monolith. Use Celery + RabbitMQ for asynchronous workers partitioned by domain (event, automation, intelligence).

## Consequences
- Simpler deployment for the core API.
- Scalability for heavy tasks via Celery workers.
