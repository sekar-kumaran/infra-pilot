import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.enums import RawEventProcessingStatus
from app.models.events import RawEvent

def test_reprocess_event_success(client: TestClient, db_session: Session, admin_token_headers):
    # Create a failed event
    event = RawEvent(
        integration_id=uuid4(),
        provider="test_provider",
        payload={"test": "data"},
        payload_hash="test_hash",
        processing_status=RawEventProcessingStatus.FAILED.value
    )
    db_session.add(event)
    db_session.commit()

    response = client.post(
        f"/api/v1/events/{event.id}/reprocess",
        headers=admin_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "PENDING"
    
    # Event should be updated to RECEIVED
    db_session.refresh(event)
    assert event.processing_status == RawEventProcessingStatus.RECEIVED.value

def test_reprocess_event_invalid_status(client: TestClient, db_session: Session, admin_token_headers):
    # Create a processed event
    event = RawEvent(
        integration_id=uuid4(),
        provider="test_provider",
        payload={"test": "data"},
        payload_hash="test_hash_2",
        processing_status=RawEventProcessingStatus.PROCESSED.value
    )
    db_session.add(event)
    db_session.commit()

    response = client.post(
        f"/api/v1/events/{event.id}/reprocess",
        headers=admin_token_headers
    )
    assert response.status_code == 400
    assert "not eligible for reprocessing" in response.json()["error"]["message"]

def test_get_job_status(client: TestClient, admin_token_headers):
    # Just check endpoint exists and handles a dummy task id
    response = client.get(
        "/api/v1/events/jobs/dummy-id",
        headers=admin_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "dummy-id"
    assert data["status"] == "PENDING" # default state for unknown task
