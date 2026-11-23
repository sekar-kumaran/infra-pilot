import time
import os
import psutil
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="CloudPulse Demo Application", version="1.0.0")

# Setup templates directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Application state
APP_STATE = {
    "app_name": "CloudPulse Enterprise Demo",
    "version": "v1.0.0",
    "environment": "production",
    "start_time": time.time(),
    "maintenance_mode": False,
    "feature_flags": {
        "enhanced_telemetry": True,
        "auto_scaling": True,
        "circuit_breaker": True,
        "debug_mode": False
    },
    "services": [
        {"name": "API Gateway", "port": 5050, "status": "UP", "version": "1.4.2", "latency": "14ms", "health": "100%"},
        {"name": "Auth Service", "port": 5051, "status": "UP", "version": "1.2.0", "latency": "22ms", "health": "99.9%"},
        {"name": "Order Processor", "port": 5052, "status": "UP", "version": "2.0.1", "latency": "38ms", "health": "99.8%"},
        {"name": "Payment Worker", "port": 5053, "status": "UP", "version": "1.8.5", "latency": "45ms", "health": "100%"}
    ]
}

def get_system_metrics():
    uptime_sec = int(time.time() - APP_STATE["start_time"])
    hours, rem = divmod(uptime_sec, 3600)
    minutes, seconds = divmod(rem, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s"
    return {
        "uptime": uptime_str,
        "uptime_seconds": uptime_sec,
        "requests_total": 14280 + int(uptime_sec * 3.5),
        "active_users": 42 + (uptime_sec % 15),
        "cpu_usage": 18.4 + (uptime_sec % 8),
        "memory_usage": 42.1 + (uptime_sec % 5),
        "disk_free_gb": 128.4
    }

# --- PAGE 1: DASHBOARD / OVERVIEW ---
@app.get("/", response_class=HTMLResponse)
async def page_dashboard(request: Request):
    metrics = get_system_metrics()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "state": APP_STATE,
        "metrics": metrics,
        "page_title": "System Overview & Dashboard"
    })

# --- PAGE 2: SERVICES & CATALOG ---
@app.get("/services", response_class=HTMLResponse)
async def page_services(request: Request):
    metrics = get_system_metrics()
    return templates.TemplateResponse("services.html", {
        "request": request,
        "state": APP_STATE,
        "metrics": metrics,
        "page_title": "Microservices Catalog"
    })

# --- PAGE 3: TELEMETRY & ANALYTICS ---
@app.get("/analytics", response_class=HTMLResponse)
async def page_analytics(request: Request):
    metrics = get_system_metrics()
    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "state": APP_STATE,
        "metrics": metrics,
        "page_title": "Telemetry & Observability"
    })

# --- PAGE 4: ADMIN & OPERATIONS ---
@app.get("/admin", response_class=HTMLResponse)
async def page_admin(request: Request):
    metrics = get_system_metrics()
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "state": APP_STATE,
        "metrics": metrics,
        "page_title": "Admin Operations & DevOps Controls"
    })

# --- API ENDPOINTS (For Nagios, Prometheus, InfraPilot) ---
@app.get("/health")
async def health_check():
    status_code = 503 if APP_STATE["maintenance_mode"] else 200
    return JSONResponse(status_code=status_code, content={
        "status": "MAINTENANCE" if APP_STATE["maintenance_mode"] else "UP",
        "app": APP_STATE["app_name"],
        "version": APP_STATE["version"],
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": int(time.time() - APP_STATE["start_time"]),
        "checks": {
            "database": "OK",
            "cache": "OK",
            "storage": "OK"
        }
    })

@app.get("/api/metrics")
async def api_metrics():
    return {
        "metrics": get_system_metrics(),
        "services": APP_STATE["services"],
        "maintenance_mode": APP_STATE["maintenance_mode"]
    }

@app.post("/api/admin/toggle-maintenance")
async def toggle_maintenance():
    APP_STATE["maintenance_mode"] = not APP_STATE["maintenance_mode"]
    return {
        "status": "success",
        "maintenance_mode": APP_STATE["maintenance_mode"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5050, reload=False)
