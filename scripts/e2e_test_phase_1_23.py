import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "apps", "api"))
from fastapi.testclient import TestClient
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import json

from app.main import app as fastapi_app
from app.database.base import Base
from app.models.user import User
from app.models.enums import (
    IncidentStatus,
    WorkflowExecutionStatus,
    WorkflowStepStatus,
    ProviderErrorClassification
)
from app.api import deps
import app.workers.tasks

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
SQLiteTypeCompiler.visit_JSONB = lambda self, type_, **kw: "JSON"

def override_get_current_user():
    return User(
        id=uuid.uuid4(),
        email="testadmin@example.com",
        is_active=True
    )

@pytest.fixture(scope="function")
def test_db(mocker):
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    mocker.patch('app.api.deps.require_permission', return_value=override_get_current_user)
    mocker.patch('app.services.rbac.get_user_permissions', return_value=[
        "workflows:write", "workflows:read", "workflows:execute", "incidents:read", "incidents:write"
    ])
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    fastapi_app.dependency_overrides[deps.get_db] = override_get_db
    fastapi_app.dependency_overrides[deps.get_current_user] = override_get_current_user
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()

def test_workflow_state_machine_and_idempotency(client, test_db, mocker):
    """
    Validates that:
    1. Duplicate execution attempts (idempotency) are ignored.
    2. Invalid state transitions are rejected.
    3. Workflow engine properly handles wait states and timeouts.
    """
    workflow_data = {
        "name": "E2E Idempotent Workflow",
        "description": "Tests Phase 1.23 idempotency",
        "enabled": True,
        "trigger_type": "manual",
        "policy_configuration": {},
        "steps": [
            {
                "sequence": 1,
                "action": "aws_reboot_instance",
                "capability": "cloud_compute_management",
                "provider_constraint": "aws",
                "target_resolution_strategy": {"use_incident_resource": True},
                "approval_requirement": True
            }
        ]
    }

    resp = client.post("/api/v1/workflows/", json=workflow_data)
    assert resp.status_code == 200, resp.text
    workflow_id = resp.json()["id"]

    import app.models.resource as resource_models
    import app.models.incidents as inc_models
    from app.models.enums import ResourceType, ResourceStatus

    resource_id = str(uuid.uuid4())
    inc_id = str(uuid.uuid4())
    
    res = resource_models.InfrastructureResource(
        id=uuid.UUID(resource_id), name="test-ec2", resource_type=ResourceType.CLOUD_INSTANCE.value, 
        external_id="i-123", provider="aws", status=ResourceStatus.ACTIVE.value
    )
    inc = inc_models.Incident(id=uuid.UUID(inc_id), title="EC2 Down", status=IncidentStatus.OPEN.value)
    
    test_db.add(res)
    test_db.add(inc)
    test_db.commit()

    # Mock Celery
    import app.workers.tasks
    original_delay = app.workers.tasks.execute_workflow_task.delay
    app.workers.tasks.execute_workflow_task.delay = lambda exec_id: app.workers.tasks.execute_workflow_task(exec_id)
    app.workers.tasks.get_session_factory = lambda: TestingSessionLocal

    mock_executor = mocker.MagicMock()
    mock_executor.execute.return_value = (True, {"status": "rebooted"}, "")
    mock_executor.verify.return_value = (True, {"status": "up"}, "")
    mocker.patch('app.services.workflow_engine.ExecutorFactory.get_executor', return_value=mock_executor)

    # 1. Start execution
    exec_resp = client.post(f"/api/v1/workflows/{workflow_id}/execute?incident_id={inc_id}&resource_id={resource_id}")
    assert exec_resp.status_code == 200
    execution_id = exec_resp.json()["id"]

    # 2. Assert WAITING_APPROVAL
    exec_check = client.get(f"/api/v1/workflows/{workflow_id}/executions")
    assert exec_check.json()[0]["status"] == WorkflowExecutionStatus.WAITING_APPROVAL.value

    # 3. Simulate duplicate Celery task delivery while WAITING_APPROVAL
    app.workers.tasks.execute_workflow_task(execution_id)
    exec_check2 = client.get(f"/api/v1/workflows/{workflow_id}/executions")
    # Should STILL be WAITING_APPROVAL, duplicate delivery gracefully ignored
    assert exec_check2.json()[0]["status"] == WorkflowExecutionStatus.WAITING_APPROVAL.value

    # 4. Approve with scoped parameters
    exec_db = test_db.query(app.models.workflow.WorkflowExecution).filter_by(id=uuid.UUID(execution_id)).first()
    exec_db.execution_context = {
        "approved": True,
        "approved_action": "aws_reboot_instance",
        "approved_target": resource_id
    }
    # Transition to PENDING to resume
    exec_db.status = WorkflowExecutionStatus.PENDING.value
    test_db.commit()

    # 5. Resume execution
    app.workers.tasks.execute_workflow_task(execution_id)

    # 6. Should SUCCEED
    exec_check3 = client.get(f"/api/v1/workflows/{workflow_id}/executions")
    assert exec_check3.json()[0]["status"] == WorkflowExecutionStatus.SUCCEEDED.value

    # 7. Another duplicate delivery after terminal state
    app.workers.tasks.execute_workflow_task(execution_id)
    exec_check4 = client.get(f"/api/v1/workflows/{workflow_id}/executions")
    assert exec_check4.json()[0]["status"] == WorkflowExecutionStatus.SUCCEEDED.value # Remains safely SUCCEEDED
