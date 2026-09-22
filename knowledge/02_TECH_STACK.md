# Tech Stack

## Purpose
Document the approved technologies for InfraPilot.

## Scope
- **Frontend**: Next.js, TypeScript, TailwindCSS, shadcn/ui, Recharts.
- **Backend**: Python, FastAPI, Pydantic, SQLAlchemy, Alembic.
- **Async/Queue**: Celery, RabbitMQ.
- **Cache**: Redis.
- **Database**: PostgreSQL.
- **Infrastructure**: Docker, Docker Compose, Kubernetes, Helm.
- **Automation Tools**: Terraform/OpenTofu, Ansible, Puppet.
- **Monitoring**: Prometheus, Alertmanager, Nagios, Grafana, Loki.
- **ML**: scikit-learn, PyTorch (only if justified).
- **CI/CD**: GitHub Actions, Argo CD.

## Decisions
- Selected standard, mature tooling that fits well with DevOps automation.

## Constraints
- Do not introduce new datastores unless strictly necessary and approved via ADR.

## Current Status
- Initial technologies selected.
