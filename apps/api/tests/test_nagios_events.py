import pytest
from unittest.mock import patch, MagicMock
from app.workers.integration_tasks import poll_nagios_status_task

@patch('app.workers.integration_tasks.get_session_factory')
@patch('app.workers.integration_tasks.AdapterRegistry')
@patch('app.services.event_ingestion.EventIngestionService')
@patch('redis.from_url')
def test_poll_nagios_status_task(mock_redis_from_url, mock_event_service, mock_registry, mock_get_session):
    mock_db = MagicMock()
    mock_get_session.return_value = MagicMock(return_value=mock_db)
    
    # Mock integrations
    mock_integration = MagicMock()
    mock_integration.id = "00000000-0000-0000-0000-000000000000"
    mock_integration.provider = "nagios"
    mock_integration.configuration = {}
    mock_integration.secret_payload = ""
    
    mock_db.query().filter().all.return_value = [mock_integration]
    
    # Mock lock
    mock_redis_conn = MagicMock()
    mock_redis_conn.set.return_value = True # Lock acquired
    mock_redis_from_url.return_value = mock_redis_conn
    
    # Mock adapter
    mock_adapter = MagicMock()
    mock_registry.get_adapter.return_value = mock_adapter
    
    mock_client = MagicMock()
    from app.integrations.providers.nagios.schemas import NagiosHostStatus, NagiosServiceStatus
    mock_client.get_status.return_value = (
        [NagiosHostStatus(host_name="test-host", current_state=2, last_state_change=100)],
        [NagiosServiceStatus(host_name="test-host", service_description="test-svc", current_state=0, last_state_change=100)]
    )
    mock_adapter._get_client.return_value = mock_client
    
    mock_event_service_instance = MagicMock()
    mock_event_service.return_value = mock_event_service_instance
    
    # Call task
    poll_nagios_status_task()
    
    # Verify ingest_event called twice
    assert mock_event_service_instance.ingest_event.call_count == 2
    
    # Check external_event_id is anchored to last_state_change
    call_args_1 = mock_event_service_instance.ingest_event.call_args_list[0][1]['event_in']
    assert "00000000-0000-0000-0000-000000000000-test-host-2-100" in call_args_1.external_event_id
    
    call_args_2 = mock_event_service_instance.ingest_event.call_args_list[1][1]['event_in']
    assert "00000000-0000-0000-0000-000000000000-test-host-test-svc-0-100" in call_args_2.external_event_id
