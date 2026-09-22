# Folder Structure

## Purpose
Document the repository layout.

## Scope
- Root directory.

## Structure
- `apps/web/`: Next.js frontend.
- `apps/api/`: FastAPI backend monolith.
- `workers/`: Celery task modules.
- `intelligence/`: ML models and correlation logic.
- `automation/`: Handlers for Terraform/Ansible execution.
- `integrations/`: Third party connectors.
- `infrastructure/`: Infrastructure definitions (Helm, manifests).
- `monitoring/`: Alerting rules and grafana dashboards for the tool itself.
- `database/`: Migrations and connection setup.
- `tests/`: End to end and cross-module tests.
- `scripts/`: Development and maintenance scripts.
- `docs/`: User documentation.
- `knowledge/`: Engineering documentation and memory (source of truth).
- `.github/`: CI/CD pipelines.

## Current Status
- Initialized.
