# InfraPilot DevOps Lab

## Overview
The InfraPilot DevOps Lab provides a containerized micro-environment to simulate a real infrastructure stack. This allows you to test InfraPilot's event-driven orchestration, incident discovery, and remediation capabilities locally without requiring active AWS or external cloud accounts.

## Components
The lab uses `docker-compose` to spin up the following services:

1. **PostgreSQL** (`db`): The primary metadata and control plane database for InfraPilot.
2. **Lab Backend API** (`backend`): A sample Python FastAPI service. It continuously receives traffic, occasionally generating simulated errors or latency.
3. **Prometheus** (`prometheus`): Scrapes metrics from the Lab Backend API to monitor HTTP request volume, latency, and status codes.
4. **Grafana** (`grafana`): Connected to Prometheus. Allows configuring alerts that trigger webhooks into InfraPilot.
5. **Ansible Target** (`ansible-target`): A generic Ubuntu container running an SSH daemon. InfraPilot uses this as a dummy target to execute shell remediation commands via the Ansible Provider.
6. **Traffic Generator** (`traffic`): A Python script sending continuous, randomized requests to the backend API to ensure Prometheus receives active metrics.

## Prerequisites
- Docker Engine / Docker Desktop
- Docker Compose v2+
- Node.js (for the frontend)
- Python 3.11 (for the backend control plane)

## Running the Lab

1. Navigate to the devops-lab directory:
   ```bash
   cd scripts/devops-lab
   ```

2. Start the lab environment:
   ```bash
   docker-compose up -d --build
   ```

3. Verify services are running:
   - Prometheus: `http://localhost:9090`
   - Grafana: `http://localhost:3001` (admin/admin)
   - Lab App: `http://localhost:8080`

## End-to-End Validation Example

1. **Connect Integrations**: Start InfraPilot backend and navigate to the UI. Enable the "Prometheus" and "Ansible" integrations, pointing Prometheus to `http://localhost:9090` and Ansible to the `ansible-target` container (`localhost:2222`).
2. **Simulate an Incident**: In Grafana, configure an alert rule for high HTTP 500s or latency on the Lab App. Configure the webhook to point to `http://<infrapilot-host>:8000/api/v1/events/prometheus`.
3. **Trigger Alert**: Modify `scripts/devops-lab/app/main.py` temporarily to force 500s, or use a script to spam the endpoint.
4. **Observe**: InfraPilot receives the webhook, evaluates the event, and opens an Incident.
5. **Automate**: Based on active Policies, InfraPilot can trigger a Workflow to SSH into `ansible-target` and simulate a "service restart" command.

## Teardown
```bash
cd scripts/devops-lab
docker-compose down -v
```
