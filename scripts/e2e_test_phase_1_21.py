import pytest
import asyncio
import os
import sys

# Add apps/api to path so it can import app modules
api_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api"))
sys.path.insert(0, api_dir)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

from app.main import app as fastapi_app
from app.api.deps import get_db, get_current_user
from app.database.base import Base
import app.models.user
import app.models.environment
import app.models.resource
import app.models.incidents
import app.models.remediation
import app.models.automation
import app.models.audit
import app.models.policy
import app.models.events
import app.models.failed_events
import app.models.integration
import app.models.resource_relationship
import app.models.rbac
from app.models.enums import ResourceType, IncidentStatus, ApprovalStatus

# Setup in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
from sqlalchemy.pool import StaticPool
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
SQLiteTypeCompiler.visit_JSONB = lambda self, type_, **kw: "JSON"

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

fastapi_app.dependency_overrides[get_db] = override_get_db

# Create a mock user
mock_user = app.models.user.User(id=uuid.uuid4(), email="test@infrapilot.com", is_active=True)
def override_get_current_user():
    return mock_user

fastapi_app.dependency_overrides[get_current_user] = override_get_current_user

# Mock RBAC
import app.services.rbac
class AllPermissionsList(list):
    def __contains__(self, item):
        return True

app.services.rbac.get_user_permissions = lambda db, user_id: AllPermissionsList()

import app.services.audit
app.services.audit.log_event = lambda *args, **kwargs: None

client = TestClient(fastapi_app)

def test_incident_orchestration_e2e():
    db = TestingSessionLocal()
    
    # 1. Create a dummy environment
    env_response = client.post("/api/v1/environments/", json={"name": "test-env", "description": "test", "environment_type": "DEVELOPMENT"})
    assert env_response.status_code in (200, 201), env_response.text
    env_id = env_response.json()["id"]
    
    # 2. Create a dummy resource
    res_response = client.post("/api/v1/resources/", json={
        "name": "test-instance",
        "resource_type": "CLOUD_INSTANCE",
        "environment_id": env_id,
        "provider": "aws",
        "external_id": "i-12345",
        "status": "ACTIVE",
        "metadata": {}
    })
    assert res_response.status_code in (200, 201), res_response.text
    res_id = res_response.json()["id"]
    
    from app.models.incidents import Incident
    # 3. Create an incident linked to this resource via DB
    new_inc = Incident(
        title="Instance Down",
        description="Instance is unreachable",
        severity="CRITICAL",
        status=IncidentStatus.OPEN.value,
        primary_resource_id=uuid.UUID(res_id)
    )
    db.add(new_inc)
    db.commit()
    db.refresh(new_inc)
    inc_id = str(new_inc.id)
    
    # 4. Get Remediation Options
    options_resp = client.get(f"/api/v1/incidents/{inc_id}/remediation-options")
    assert options_resp.status_code == 200
    options = options_resp.json()
    # At least one strategy should be proposed
    assert len(options) > 0
    
    # Let's pick the first one (e.g. restart_instance)
    strategy = options[0]["strategy"]
    
    # 5. Create Remediation Plan
    plan_resp = client.post(f"/api/v1/incidents/{inc_id}/remediation", json={"strategy": strategy, "parameters": {}})
    assert plan_resp.status_code in (200, 201), plan_resp.text
    plan = plan_resp.json()
    assert plan["strategy"] == strategy
    
    # Verify incident state changed
    inc_verify = client.get(f"/api/v1/incidents/{inc_id}")
    assert inc_verify.json()["status"] in [IncidentStatus.REMEDIATION_PENDING.value, IncidentStatus.APPROVAL_REQUIRED.value]
    
    # 6. Approve Remediation Plan
    if plan["requires_approval"]:
        approve_resp = client.post(f"/api/v1/remediation/{plan['id']}/approve")
        assert approve_resp.status_code in (200, 201), approve_resp.text
        assert approve_resp.json()["approval_status"] == ApprovalStatus.APPROVED.value
        
    # Mock celery delay to execute synchronously for the test
    import app.workers.tasks
    import app.database.session
    original_delay = app.workers.tasks.execute_remediation_task.delay
    original_session = app.database.session.get_session_factory
    
    app.workers.tasks.execute_remediation_task.delay = lambda plan_id: app.workers.tasks.execute_remediation_task(plan_id)
    app.workers.tasks.get_session_factory = lambda: TestingSessionLocal
    app.database.session.get_session_factory = lambda: TestingSessionLocal
    
    try:
        # 7. Execute Remediation Plan
        exec_resp = client.post(f"/api/v1/remediation/{plan['id']}/execute")
        assert exec_resp.status_code in (200, 201), exec_resp.text
        
        # 8. Verify final states
        plan_verify = client.get(f"/api/v1/remediation/{plan['id']}")
        assert plan_verify.status_code == 200
        plan_data = plan_verify.json()
        
        # Depending on the mocked executor, it might succeed or fail, but it should not be PENDING
        assert plan_data["execution_status"] in ["SUCCEEDED", "FAILED", "RUNNING", "VERIFYING"]
        
        inc_final = client.get(f"/api/v1/incidents/{inc_id}")
        # Incident should be RECOVERED or ESCALATED based on executor
        assert inc_final.json()["status"] in ["RECOVERED", "ESCALATED"]
    finally:
        app.workers.tasks.execute_remediation_task.delay = original_delay
        app.workers.tasks.get_session_factory = original_session
        app.database.session.get_session_factory = original_session

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
