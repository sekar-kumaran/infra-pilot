"""
InfraPilot Standalone FastAPI Control Plane Server (v2.2.0).
Includes endpoints for:
- Per-Container & Per-Tool Logs (/api/v1/resources/{id}/logs, /api/v1/integrations/{id}/logs)
- Interactive Container / Pod / Microservice Shell Exec (/api/v1/resources/{id}/exec)
- Jenkins CI/CD Pipeline Control (/api/v1/jenkins/pipelines, /api/v1/jenkins/build)
- GitHub Copilot Enterprise & SRE Agent Control (/api/v1/copilot/status, /api/v1/copilot/analyze, /api/v1/copilot/policy)
"""

from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from .store import ControlPlaneStore, PROVIDER_CAPABILITIES, DEFAULT_DB_PATH

store = ControlPlaneStore(db_path=DEFAULT_DB_PATH)

app = FastAPI(
    title="InfraPilot Control Plane API",
    version="2.2.0",
    description="Enterprise SRE & DevOps Tool Orchestration, Container Exec, Log Multiplexing & Automation Control Plane",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health/live")
def health_live():
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready():
    return {"status": "ready"}


@app.get("/health")
def health_root():
    return {"status": "ok", "service": "infrapilot-control-plane", "version": "2.2.0"}


@app.get("/api/v1/system/info")
def system_info():
    return {"application_name": "InfraPilot Control Plane", "version": "2.2.0", "environment": "production"}


@app.get("/api/v1/system/metrics-summary")
def system_metrics_summary():
    return store.get_metrics_summary()


@app.get("/api/v1/providers/capabilities")
def get_provider_capabilities():
    return PROVIDER_CAPABILITIES


# --- Applications ---
@app.get("/api/v1/applications")
@app.get("/api/v1/applications/")
def list_applications():
    return store.list_applications()


# --- Integrations / DevOps Tools ---
@app.get("/api/v1/integrations")
@app.get("/api/v1/integrations/")
def list_integrations():
    return store.list_integrations()


@app.get("/api/v1/integrations/{integration_id}/logs")
def get_integration_logs(integration_id: str, level: Optional[str] = None, query: Optional[str] = None, tail: int = 100):
    return store.get_target_logs(integration_id, level=level, query=query, tail=tail)


@app.post("/api/v1/integrations/webhook/prometheus")
def prometheus_webhook(payload: Dict[str, Any] = Body(...)):
    alerts = payload.get("alerts", [])
    if not alerts and payload.get("status"):
        alerts = [payload]
    ingested = []
    for alert in alerts:
        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})
        alertname = labels.get("alertname", "PrometheusAlert")
        sev = labels.get("severity", "CRITICAL").upper()
        res_ext = alert.get("resource") or labels.get("job") or "res-nexus-gw"
        ev = store.ingest_event(
            provider="prometheus",
            event_type="prometheus_firing",
            payload={
                "title": f"[{alertname}] {annotations.get('summary', alertname)}",
                "description": annotations.get("description", "Threshold breached in Prometheus Alertmanager"),
                "severity": sev,
                "labels": labels,
                "resource": res_ext,
            },
            resource_external_id=res_ext,
            integration_id="int-prom-01",
        )
        ingested.append(ev)
    return {"status": "ok", "alerts_received": len(alerts), "new_events_ingested": len(ingested), "events": ingested}


# --- Resources, Logs & Interactive Shell Exec ---
@app.get("/api/v1/resources")
@app.get("/api/v1/resources/")
def list_resources(provider: Optional[str] = None, resource_type: Optional[str] = None, status: Optional[str] = None):
    items = store.list_resources(provider=provider, resource_type=resource_type, status=status)
    return {"items": items, "total": len(items), "page": 1, "page_size": 100}


@app.get("/api/v1/resources/{resource_id}/logs")
def get_resource_logs(resource_id: str, level: Optional[str] = None, query: Optional[str] = None, tail: int = 100):
    return store.get_target_logs(resource_id, level=level, query=query, tail=tail)


@app.post("/api/v1/resources/{resource_id}/exec")
def exec_in_resource(resource_id: str, payload: Dict[str, Any] = Body(...)):
    command = payload.get("command", "ps aux")
    shell = payload.get("shell", "bash")
    return store.exec_in_target(resource_id, command=command, shell=shell)


@app.post("/api/v1/resources/{resource_id}/actions/{action}")
def perform_resource_action(resource_id: str, action: str, payload: Optional[Dict[str, Any]] = Body(default=None)):
    try:
        return store.perform_resource_action(resource_id, action, payload or {})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/v1/infrastructure/topology")
def get_topology():
    return store.get_topology()


# --- Jenkins CI/CD API Control ---
@app.get("/api/v1/jenkins/pipelines")
def list_jenkins_pipelines():
    return store.list_jenkins_pipelines()


@app.post("/api/v1/jenkins/build")
def trigger_jenkins_build(payload: Dict[str, Any] = Body(...)):
    try:
        return store.trigger_jenkins_build(
            pipeline_id_or_name=payload.get("pipeline", "nexuspay-prod-release"),
            branch=payload.get("branch", "main"),
            tag=payload.get("tag", "v2.3.2"),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- GitHub Copilot Enterprise & SRE Agent API Control ---
@app.get("/api/v1/copilot/status")
def get_copilot_status():
    return store.get_copilot_state()


@app.post("/api/v1/copilot/analyze")
def copilot_analyze(payload: Dict[str, Any] = Body(...)):
    return store.copilot_analyze_target(payload.get("target", "res-nexus-worker"))


@app.post("/api/v1/copilot/policy")
def copilot_policy(payload: Dict[str, Any] = Body(...)):
    return store.update_copilot_policy(
        public_code=payload.get("public_code_suggestions"),
        cli_shell=payload.get("cli_in_prod_shells"),
    )


# --- Incidents, Automation, Policies & Audit ---
@app.get("/api/v1/incidents")
@app.get("/api/v1/incidents/")
def list_incidents(status: Optional[str] = None, severity: Optional[str] = None):
    return store.list_incidents(status=status, severity=severity)


@app.get("/api/v1/automation/playbooks")
def list_playbooks():
    return store.list_playbooks()


@app.post("/api/v1/automation/executions", status_code=201)
def trigger_execution(payload: Dict[str, Any] = Body(...)):
    return store.trigger_execution(
        playbook_id=payload["playbook_id"],
        trigger_type=payload.get("trigger_type", "MANUAL"),
        trigger_source=payload.get("trigger_source", "console"),
        incident_id=payload.get("incident_id"),
        resource_id=payload.get("resource_id"),
        force_auto_approve=bool(payload.get("force_auto_approve", False)),
    )


@app.get("/api/v1/automation/approvals")
def list_approvals():
    return store.list_approvals()


@app.post("/api/v1/automation/approvals/{approval_id}/action")
def action_approval(approval_id: str, payload: Dict[str, Any] = Body(...)):
    return store.decide_approval(approval_id, payload.get("action", "APPROVE"), payload.get("reason", "Approved"))


@app.post("/api/v1/policies/simulate")
def simulate_policy(payload: Dict[str, Any] = Body(...)):
    return store.simulate_policy(payload)


@app.get("/api/v1/audit")
def list_audit(limit: int = 100):
    items = store.list_audit_events(limit=limit)
    return {"items": items, "total": len(items)}
