import os
import sys
import uuid
from sqlalchemy.orm import Session

# Add the apps/api directory to sys.path so we can import app modules
api_path = os.path.join(os.path.dirname(__file__), "..", "apps", "api")
sys.path.append(api_path)

from app.database.session import get_session_factory
from app.integrations.registry import AdapterRegistry
from app.models.enums import ResourceType, ProviderType
from app.models.workflow import OperationWorkflow
from app.services.event_trigger import EventTriggerService
from app.models.incidents import Incident
from app.models.events import Alert

def test_grafana_provider():
    print("\n--- Testing Grafana Provider Registration ---")
    adapter = AdapterRegistry.get_adapter("grafana")
    if not adapter:
        print("[FAIL] Grafana Provider NOT registered.")
        return False
        
    print("✅ Grafana Provider registered successfully.")
    
    cap = adapter.get_capabilities()
    print(f"Resource Discovery: {cap.resource_discovery}")
    print(f"Metrics Read: {cap.metrics_read}")
    
    if cap.resource_discovery:
        print("[PASS] Grafana handles resource discovery.")
    else:
        print("[FAIL] Grafana is missing resource discovery capability.")
        return False
        
    return True

def test_event_trigger_service():
    print("\n--- Testing Event Trigger Service ---")
    db = get_session_factory()()
    
    try:
        # Create a mock trigger workflow
        workflow = OperationWorkflow(
            name="Test Alert Workflow",
            trigger_type="event",
            trigger_conditions=[
                {"provider": "grafana", "severity": "CRITICAL"}
            ],
            enabled=True
        )
        db.add(workflow)
        db.commit()
        db.refresh(workflow)
        
        # Create a mock incident
        incident = Incident(
            id=uuid.uuid4(),
            title="Grafana Critical Test",
            severity="CRITICAL",
            status="open",
            source="grafana",
            correlation_key="test_grafana_trigger"
        )
        db.add(incident)
        db.commit()
        
        # Add mock alert
        alert = Alert(
            id=uuid.uuid4(),
            raw_event_id=uuid.uuid4(),
            integration_id=uuid.uuid4(),
            provider="grafana",
            alert_type="CPU_HIGH",
            severity="CRITICAL",
            title="CPU Is high",
            fingerprint="test_fingerprint",
            status="active"
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        # Link alert to incident manually for the test
        incident.related_alerts = [str(alert.id)]
        db.commit()
        
        service = EventTriggerService(db)
        executions = service.evaluate_and_trigger(incident)
        
        if len(executions) > 0:
            print(f"✅ EventTriggerService successfully matched {len(executions)} workflows.")
            for e in executions:
                print(f"  -> Execution ID: {e.id}")
        else:
            print("❌ EventTriggerService failed to trigger workflow.")
            return False
            
    finally:
        db.rollback()
        db.close()
        
    return True

if __name__ == "__main__":
    passed = True
    passed = passed and test_grafana_provider()
    passed = passed and test_event_trigger_service()
    
    if passed:
        print("\n🎉 Phase 1.24 automated backend tests passed!")
    else:
        print("\n💥 Tests failed.")
        sys.exit(1)
