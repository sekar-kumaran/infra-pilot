import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.main import create_app
from app.database.session import get_db

def test_prometheus_webhook_ingestion():
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    mock_integration = Mock()
    mock_integration.id = "00000000-0000-0000-0000-000000000001"
    
    test_app = create_app()
    test_app.dependency_overrides[get_db] = lambda: mock_db
    
    webhook_payload = {
        "receiver": "infrapilot-webhook",
        "status": "firing",
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "WeatherApiHighErrorRate",
                    "severity": "CRITICAL",
                    "service": "weather-backend",
                    "job": "weather-api",
                    "instance": "demo_app_api:4000"
                },
                "annotations": {
                    "summary": "Weather API is experiencing high error rate",
                    "description": "The weather API has returned 500 errors in the last minute."
                },
                "startsAt": "2026-10-26T12:00:00Z"
            }
        ]
    }
    
    with patch("app.services.event_ingestion.EventIngestionService.ingest_event") as mock_ingest:
        mock_raw_event = Mock()
        mock_ingest.return_value = (mock_raw_event, True)
        
        with TestClient(test_app) as client:
            response = client.post("/api/v1/integrations/webhook/prometheus", json=webhook_payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["alerts_received"] == 1
            assert data["new_events_ingested"] == 1
            assert mock_ingest.called
