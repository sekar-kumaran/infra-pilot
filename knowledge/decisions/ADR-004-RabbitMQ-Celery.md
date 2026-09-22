# ADR-004: RabbitMQ and Celery

## Status
Accepted

## Context
We need a reliable message broker to distribute long-running tasks like Terraform applies and ML inference.

## Decision
Use RabbitMQ as the broker and Celery as the worker framework.

## Consequences
- Robust retries and visibility into queues.
- Redis will serve as the result backend if needed.
