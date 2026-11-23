"""InfraPilot v2.6.0 Production FastAPI Control Plane Server."""
import os
from typing import Any, Dict
from fastapi import FastAPI, Body, HTTPException
from fastapi.responses import HTMLResponse
from .store import ControlPlaneStore, DEFAULT_DB_PATH

store = ControlPlaneStore(db_path=DEFAULT_DB_PATH)
app = FastAPI(title="InfraPilot Production Control Plane API", version="2.6.0")

def seed_demo_integrations():
    """Seed the Demo Application and DevOps tools (Nagios, Ansible, Terraform) if not already present."""
    existing_tools = {t["name"]: t for t in store.list_integrations()}
    
    tools_to_seed = [
        {
            "name": "CloudPulse 4-Page Demo Application",
            "provider": "CUSTOM SDK",
            "endpoint": "http://127.0.0.1:5050",
            "description": "Production 4-page microservice demo suite (Overview, Services, Analytics, Admin)"
        },
        {
            "name": "Nagios Monitoring Core",
            "provider": "NAGIOS",
            "endpoint": "http://127.0.0.1:9090/nagios/status.dat",
            "description": "Nagios Core 4.4 monitoring host and all 4 application page endpoints"
        },
        {
            "name": "Ansible Automation Engine",
            "provider": "ANSIBLE",
            "endpoint": "http://127.0.0.1:9090/ansible",
            "description": "Ansible automation runner managing multi-node deployment & service playbooks"
        },
        {
            "name": "Terraform Cloud & IaC",
            "provider": "TERRAFORM",
            "endpoint": "http://127.0.0.1:9090/terraform",
            "description": "Terraform Cloud workspace (cloudpulse-production) managing infrastructure"
        }
    ]

    for t in tools_to_seed:
        if t["name"] not in existing_tools:
            store.create_integration(
                name=t["name"],
                provider=t["provider"],
                endpoint=t["endpoint"],
                description=t["description"]
            )

    existing_workloads = {w["name"]: w for w in store.list_resources()}
    workloads_to_seed = [
        {"name": "cloudpulse-api-gateway", "provider": "docker", "resource_type": "CONTAINER", "metadata": {"port": 5050, "role": "gateway", "status": "UP"}},
        {"name": "cloudpulse-auth-service", "provider": "docker", "resource_type": "CONTAINER", "metadata": {"port": 5051, "role": "auth", "status": "UP"}},
        {"name": "cloudpulse-order-engine", "provider": "docker", "resource_type": "CONTAINER", "metadata": {"port": 5052, "role": "orders", "status": "UP"}},
        {"name": "cloudpulse-payment-worker", "provider": "docker", "resource_type": "CONTAINER", "metadata": {"port": 5053, "role": "payments", "status": "UP"}}
    ]

    for w in workloads_to_seed:
        if w["name"] not in existing_workloads:
            store.register_resource(
                name=w["name"],
                provider=w["provider"],
                resource_type=w["resource_type"],
                metadata=w["metadata"]
            )

# Execute seed on module load
try:
    seed_demo_integrations()
except Exception as e:
    print(f"Notice: Seeding demo integrations: {e}")


@app.get("/", response_class=HTMLResponse)
@app.get("/control-plane", response_class=HTMLResponse)
def control_plane_ui():
    """Serve the complete InfraPilot Enterprise Control Plane UI."""
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "infrapilot_control_plane.html"),
        os.path.join(os.path.dirname(__file__), "infrapilot_control_plane.html"),
        os.path.join(os.getcwd(), "infrapilot_control_plane.html"),
        os.path.join(os.getcwd(), "infrapilot", "infrapilot_control_plane.html"),
    ]
    for path in candidates:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
    return "<h1>InfraPilot Control Plane HTML not found</h1>"


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.6.0"}


@app.post("/api/v1/auth/login")
def login(payload: Dict[str, Any] = Body(...)):
    user = store.authenticate(payload.get("username", ""), payload.get("password", ""))
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials. Default bootstrap login is admin / admin.")
    return {"status": "authenticated", "user": user}


@app.post("/api/v1/auth/change-password")
def change_password(payload: Dict[str, Any] = Body(...)):
    try:
        user = store.change_password(
            payload.get("username", "admin"),
            payload.get("current_password", ""),
            payload.get("new_password", ""),
        )
        return {"status": "password_updated", "user": user}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/system/metrics-summary")
def metrics_summary():
    tools = store.list_integrations()
    workloads = store.list_resources()
    return {
        "status": "ONLINE",
        "connected_tools": len(tools),
        "total_workloads": len(workloads),
    }


@app.get("/api/v1/integrations")
def list_integrations():
    return store.list_integrations()


@app.post("/api/v1/integrations")
def create_integration(payload: Dict[str, Any] = Body(...)):
    return store.create_integration(
        name=payload.get("name", "Tool"),
        provider=payload.get("provider", "DOCKER"),
        endpoint=payload.get("endpoint", ""),
        description=payload.get("description", ""),
    )


@app.get("/api/v1/resources")
def list_resources():
    return store.list_resources()


@app.post("/api/v1/resources")
def create_resource(payload: Dict[str, Any] = Body(...)):
    return store.register_resource(
        name=payload.get("name", "workload"),
        provider=payload.get("provider", "docker"),
        resource_type=payload.get("resource_type", "CONTAINER"),
        metadata=payload.get("metadata", {}),
    )
