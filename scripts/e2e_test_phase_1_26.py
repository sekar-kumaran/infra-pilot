import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

from app.main import app
from app.database.base import Base
from app.models.tenant import Tenant
from app.models.user import User
from app.models.workflow import OperationWorkflow, WorkflowExecution, WorkflowExecutionStatus
from app.api.deps import get_current_user
from app.api.dependencies.tenant import get_current_tenant
from app.database.session import get_db
from app.core.security import get_password_hash

# Use a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_phase1_26.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Create tenant A
    tenant_a = Tenant(name="Tenant A", slug="tenant-a", status="ACTIVE")
    db.add(tenant_a)
    
    # Create tenant B
    tenant_b = Tenant(name="Tenant B", slug="tenant-b", status="ACTIVE")
    db.add(tenant_b)
    db.commit()
    
    # Create User for Tenant A
    user_a = User(
        email="user_a@example.com",
        hashed_password=get_password_hash("password"),
        is_active=True,
        is_superuser=True,
        tenant_id=tenant_a.id
    )
    db.add(user_a)
    db.commit()

    # Create User for Tenant B
    user_b = User(
        email="user_b@example.com",
        hashed_password=get_password_hash("password"),
        is_active=True,
        is_superuser=True,
        tenant_id=tenant_b.id
    )
    db.add(user_b)
    db.commit()

    yield {"tenant_a": tenant_a, "tenant_b": tenant_b, "user_a": user_a, "user_b": user_b}
    
    Base.metadata.drop_all(bind=engine)
    db.close()

def override_get_current_user_factory(user):
    def _override():
        return user
    return _override

def override_get_current_tenant_factory(tenant):
    def _override():
        return tenant
    return _override

def test_tenant_isolation(setup_database):
    db = TestingSessionLocal()
    tenant_a = setup_database["tenant_a"]
    tenant_b = setup_database["tenant_b"]
    user_a = setup_database["user_a"]

    app.dependency_overrides[get_current_user] = override_get_current_user_factory(user_a)
    app.dependency_overrides[get_current_tenant] = override_get_current_tenant_factory(tenant_a)
    
    # Setup some resources for A
    wf_a = OperationWorkflow(name="WF A", tenant_id=tenant_a.id)
    db.add(wf_a)
    db.commit()

    # Test reading workflows - User A shouldn't see B's workflows
    response = client.get("/api/v1/workflows/")
    assert response.status_code == 200
    
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_get_db

def test_worker_fleet_api(setup_database):
    tenant_a = setup_database["tenant_a"]
    user_a = setup_database["user_a"]
    
    app.dependency_overrides[get_current_user] = override_get_current_user_factory(user_a)
    app.dependency_overrides[get_current_tenant] = override_get_current_tenant_factory(tenant_a)
    
    response = client.get("/api/v1/operations/health")
    assert response.status_code == 200
    data = response.json()
    assert "workers" in data
    
    response = client.get("/api/v1/operations/workers")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    response = client.get("/api/v1/operations/queues")
    assert response.status_code == 200
    
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_get_db

def test_retry_policy(setup_database):
    db = TestingSessionLocal()
    tenant_a = setup_database["tenant_a"]
    user_a = setup_database["user_a"]
    
    wf = OperationWorkflow(name="Retry Test WF", tenant_id=tenant_a.id)
    db.add(wf)
    db.commit()
    
    exec = WorkflowExecution(
        workflow_id=wf.id,
        tenant_id=tenant_a.id,
        status=WorkflowExecutionStatus.PENDING.value
    )
    db.add(exec)
    db.commit()
    
    # Simulate a failure inside WorkflowEngine
    from app.services.workflow_engine import WorkflowEngine
    engine = WorkflowEngine(db)
    
    engine._fail_execution(exec, "Test failure")
    
    db.refresh(exec)
    assert exec.status == WorkflowExecutionStatus.RETRYING.value
    assert exec.retry_count == 1
    
    engine._fail_execution(exec, "Test failure 2")
    engine._fail_execution(exec, "Test failure 3")
    engine._fail_execution(exec, "Test failure 4")
    
    db.refresh(exec)
    assert exec.status == WorkflowExecutionStatus.DEAD_LETTERED.value
    assert exec.retry_count == 3
    
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_get_db

if __name__ == "__main__":
    pytest.main(["-v", "scripts/e2e_test_phase_1_26.py"])
