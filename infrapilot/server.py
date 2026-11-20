"""InfraPilot v2.6.0 Production FastAPI Control Plane Server."""
from typing import Any, Dict
from fastapi import FastAPI, Body, HTTPException
from .store import ControlPlaneStore, DEFAULT_DB_PATH

store = ControlPlaneStore(db_path=DEFAULT_DB_PATH)
app = FastAPI(title="InfraPilot Production Control Plane API", version="2.6.0")


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
