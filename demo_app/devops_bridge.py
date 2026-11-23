"""
DevOps Provider Bridge for InfraPilot.
Provides live adapter-compliant API endpoints for:
1. Ansible Automation Runner (/ansible)
2. Nagios Core Monitoring (/nagios)
3. Terraform Cloud & Enterprise (/terraform)
"""
import os
from fastapi import FastAPI, Response, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="DevOps Provider Bridge for InfraPilot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NAGIOS_STATUS_FILE = os.path.join(BASE_DIR, "nagios", "status.dat")

# ============================================================================
# 1. ANSIBLE AUTOMATION RUNNER API
# ============================================================================
@app.get("/ansible/health")
async def ansible_health():
    """Health check endpoint expected by InfraPilot AnsibleAdapter."""
    return {
        "status": "ok",
        "service": "Ansible Automation Engine",
        "version": "2.15.3",
        "active_playbooks": 0
    }

@app.get("/ansible/api/v1/inventory")
async def ansible_inventory():
    """Inventory discovery endpoint expected by InfraPilot AnsibleAdapter."""
    return {
        "hosts": [
            {
                "name": "cloudpulse-app-node-01",
                "address": "127.0.0.1:5050",
                "groups": ["cloudpulse_app", "production", "web_tier"]
            },
            {
                "name": "cloudpulse-auth-node-02",
                "address": "127.0.0.1:5051",
                "groups": ["cloudpulse_app", "production", "auth_tier"]
            },
            {
                "name": "cloudpulse-order-node-03",
                "address": "127.0.0.1:5052",
                "groups": ["cloudpulse_app", "production", "order_tier"]
            },
            {
                "name": "cloudpulse-payment-node-04",
                "address": "127.0.0.1:5053",
                "groups": ["cloudpulse_app", "production", "worker_tier"]
            }
        ]
    }

# ============================================================================
# 2. NAGIOS MONITORING CORE API
# ============================================================================
@app.get("/nagios/health")
async def nagios_health():
    return {"status": "ok", "service": "Nagios Core", "version": "4.4.6"}

@app.get("/nagios/status.dat")
async def nagios_status():
    """Returns raw status.dat formatted text for InfraPilot NagiosStatusParser."""
    if os.path.exists(NAGIOS_STATUS_FILE):
        with open(NAGIOS_STATUS_FILE, "r") as f:
            content = f.read()
    else:
        content = """info {
    version=4.4.6
}
hoststatus {
    host_name=CloudPulse-App-Server
    current_state=0
    plugin_output=PING OK
}
servicestatus {
    host_name=CloudPulse-App-Server
    service_description=Health Check
    current_state=0
    plugin_output=HTTP 200 OK
}
"""
    return Response(content=content, media_type="text/plain")

@app.get("/nagios/cgi-bin/status.cgi")
async def nagios_cgi_status():
    return await nagios_status()

# ============================================================================
# 3. TERRAFORM CLOUD / ENTERPRISE API
# ============================================================================
@app.get("/terraform/health")
async def terraform_health():
    return {"status": "ok", "service": "Terraform Cloud API", "version": "v2"}

@app.get("/terraform/api/v2/account/details")
async def terraform_account_details():
    """Account check endpoint expected by InfraPilot TerraformClient."""
    return {
        "data": {
            "id": "user-infrapilot-operator",
            "type": "users",
            "attributes": {
                "username": "infrapilot-devops",
                "email": "devops@cloudpulse.internal"
            }
        }
    }

@app.get("/terraform/api/v2/organizations")
async def terraform_organizations():
    return {
        "data": [
            {
                "id": "org-cloudpulse-ent",
                "type": "organizations",
                "attributes": {
                    "name": "cloudpulse-enterprise",
                    "email": "devops@cloudpulse.internal"
                }
            }
        ]
    }

@app.get("/terraform/api/v2/organizations/{org}/workspaces")
async def terraform_workspaces(org: str):
    return {
        "data": [
            {
                "id": "ws-cloudpulse-prod",
                "type": "workspaces",
                "attributes": {
                    "name": "cloudpulse-production",
                    "environment": "production",
                    "resource-count": 4,
                    "terraform-version": "1.5.7",
                    "auto-apply": True,
                    "updated-at": "2026-11-23T10:00:00.000Z"
                }
            }
        ]
    }

@app.get("/terraform/api/v2/workspaces/{workspace_id}/runs")
async def terraform_runs(workspace_id: str):
    return {
        "data": [
            {
                "id": "run-98124a",
                "type": "runs",
                "attributes": {
                    "status": "applied",
                    "message": "Provisioned CloudPulse 4-Page Workload",
                    "is-destroy": False,
                    "created-at": "2026-11-23T09:30:00.000Z"
                }
            }
        ]
    }

@app.get("/terraform/api/v2/workspaces/{workspace_id}/current-state-version-outputs")
async def terraform_outputs(workspace_id: str):
    return {
        "data": [
            {
                "id": "out-app-url",
                "type": "state-version-outputs",
                "attributes": {
                    "name": "app_url",
                    "value": "http://localhost:5050",
                    "type": "string",
                    "sensitive": False
                }
            },
            {
                "id": "out-health-endpoint",
                "type": "state-version-outputs",
                "attributes": {
                    "name": "health_endpoint",
                    "value": "http://localhost:5050/health",
                    "type": "string",
                    "sensitive": False
                }
            }
        ]
    }

# ============================================================================
# OVERVIEW PORTAL
# ============================================================================
@app.get("/", response_class=HTMLResponse)
async def bridge_portal():
    return """<!DOCTYPE html>
<html>
<head>
    <title>DevOps Provider Bridge for InfraPilot</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #0f172a; color: #f8fafc; padding: 40px; }
        .card { background: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid #334155; }
        .tag { display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; }
        .tag-green { background: #065f46; color: #34d399; }
        .mono { font-family: monospace; color: #38bdf8; }
        a { color: #60a5fa; text-decoration: none; }
    </style>
</head>
<body>
    <h1>⚡ DevOps Provider Bridge for InfraPilot</h1>
    <p style="color:#94a3b8;">Active Mock &amp; Live Adapter Services for Terraform, Ansible, and Nagios.</p>
    
    <div class="card">
        <span class="tag tag-green">READY</span>
        <h3 style="margin: 8px 0;">🔴 Ansible Automation Engine</h3>
        <p>Health: <a class="mono" href="/ansible/health">/ansible/health</a> &bull; Inventory: <a class="mono" href="/ansible/api/v1/inventory">/ansible/api/v1/inventory</a></p>
    </div>

    <div class="card">
        <span class="tag tag-green">READY</span>
        <h3 style="margin: 8px 0;">🟢 Nagios Monitoring Core</h3>
        <p>Health: <a class="mono" href="/nagios/health">/nagios/health</a> &bull; Status File: <a class="mono" href="/nagios/status.dat">/nagios/status.dat</a></p>
    </div>

    <div class="card">
        <span class="tag tag-green">READY</span>
        <h3 style="margin: 8px 0;">🟣 Terraform Cloud &amp; IaC</h3>
        <p>Health: <a class="mono" href="/terraform/health">/terraform/health</a> &bull; Workspaces: <a class="mono" href="/terraform/api/v2/organizations/cloudpulse-enterprise/workspaces">/terraform/api/v2/workspaces</a></p>
    </div>
</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("devops_bridge:app", host="0.0.0.0", port=9090, reload=False)
