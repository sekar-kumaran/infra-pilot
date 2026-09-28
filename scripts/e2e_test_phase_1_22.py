import pytest
import os
import sys
import uuid
import asyncio

api_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api"))
sys.path.insert(0, api_dir)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app as fastapi_app
from app.api.deps import get_db, get_current_user
from app.database.base import Base
from app.models.enums import WorkflowExecutionStatus, WorkflowStepStatus, IncidentStatus, ResourceType, ProviderType
from app.models.user import User

# Add models so they get registered
import app.models.workflow
import app.models.incidents
import app.models.resource
import app.models.integration

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

def override_get_current_user():
    return User(id=uuid.uuid4(), email="test@infrapilot.com", is_active=True)

fastapi_app.dependency_overrides[get_db] = override_get_db
fastapi_app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(fastapi_app)

@pytest.fixture
def test_db(mocker):
    db = TestingSessionLocal()
    mocker.patch('app.api.deps.require_permission', return_value=override_get_current_user)
    mocker.patch('app.services.rbac.get_user_permissions', return_value=["workflows:write", "workflows:read", "workflows:execute", "incidents:read"])
    try:
        yield db
    finally:
        db.close()

def test_workflow_validation_and_execution_e2e(test_db, mocker):
    # 1. Create a Workflow
    workflow_data = {
        "name": "E2E Recovery Workflow",
        "description": "Cross provider recovery",
        "enabled": True,
        "trigger_type": "manual",
        "steps": [
            {
                "sequence": 1,
                "action": "aws_reboot_instance",
                "capability": "cloud_compute_management",
                "provider_constraint": "aws",
                "target_resolution_strategy": {"use_incident_resource": True},
                "verification_strategy": {
                    "provider": "prometheus",
                    "action": "prometheus_query",
                    "capability": "metrics_read",
                    "expected_state": {"status": "up"}
                }
            }
        ]
    }
    
    resp = client.post("/api/v1/workflows/", json=workflow_data)
    assert resp.status_code == 200, resp.text
    workflow = resp.json()
    assert workflow["id"]
    workflow_id = workflow["id"]
    
    # 2. Validate Workflow (dry run)
    val_resp = client.post(f"/api/v1/workflows/{workflow_id}/validate")
    assert val_resp.status_code == 200, val_resp.text
    assert val_resp.json()["valid"] is True, val_resp.json()["errors"]
    
    # 3. Create mock Incident and Resource
    resource_id = str(uuid.uuid4())
    inc_id = str(uuid.uuid4())
    from app.models.resource import InfrastructureResource
    from app.models.incidents import Incident
    
    from app.models.enums import ResourceStatus
    res = InfrastructureResource(id=uuid.UUID(resource_id), name="test-ec2", resource_type=ResourceType.CLOUD_INSTANCE.value, external_id="i-123", provider="aws", status=ResourceStatus.ACTIVE.value)
    inc = Incident(id=uuid.UUID(inc_id), title="EC2 Down", status=IncidentStatus.OPEN.value)
    
    test_db.add(res)
    test_db.add(inc)
    test_db.commit()
    
    # Mock celery task to execute synchronously
    import app.workers.tasks
    import app.database.session
    original_delay = app.workers.tasks.execute_workflow_task.delay
    app.workers.tasks.execute_workflow_task.delay = lambda execution_id: app.workers.tasks.execute_workflow_task(execution_id)
    app.workers.tasks.get_session_factory = lambda: TestingSessionLocal
    app.database.session.get_session_factory = lambda: TestingSessionLocal
    
    # Mock ExecutorFactory to return a mock executor for testing
    mock_executor = mocker.MagicMock()
    mock_executor.execute.return_value = (True, {"status": "rebooted"}, "")
    mock_executor.verify.return_value = (True, {"status": "up"}, "")
    mocker.patch('app.services.workflow_engine.ExecutorFactory.get_executor', return_value=mock_executor)
    
    try:
        # 4. Execute Workflow
        exec_resp = client.post(f"/api/v1/workflows/{workflow_id}/execute?incident_id={inc_id}&resource_id={resource_id}")
        assert exec_resp.status_code == 200, exec_resp.text
        execution_id = exec_resp.json()["id"]
        
        # 5. Check Execution Status - should be WAITING_APPROVAL because aws_reboot_instance requires approval
        exec_check = client.get(f"/api/v1/workflows/{workflow_id}/executions")
        assert exec_check.status_code == 200
        executions = exec_check.json()
        assert len(executions) == 1
        execution = executions[0]
        assert execution["status"] == WorkflowExecutionStatus.WAITING_APPROVAL.value, execution.get("failure_reason")
        
        # 6. Approve execution in DB and re-trigger
        exec_db = test_db.query(app.models.workflow.WorkflowExecution).filter_by(id=uuid.UUID(execution_id)).first()
        exec_db.execution_context = {"approved": True}
        exec_db.status = WorkflowExecutionStatus.PENDING.value
        test_db.commit()
        
        # Manually trigger task again to simulate resume
        app.workers.tasks.execute_workflow_task(execution_id)
        
        # 7. Check final status
        exec_check = client.get(f"/api/v1/workflows/{workflow_id}/executions")
        execution = exec_check.json()[0]
        assert execution["status"] == WorkflowExecutionStatus.SUCCEEDED.value
        
        inc_check = client.get(f"/api/v1/incidents/{inc_id}")
        # Incident should be RECOVERED
        assert inc_check.json()["status"] == IncidentStatus.RECOVERED.value
        
    finally:
        app.workers.tasks.execute_workflow_task.delay = original_delay

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
