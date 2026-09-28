import pytest
from app.models.events import Alert
from app.services.correlation_rules import CorrelationEngine, SameResourceRule, GlobalAlertRule

def test_same_resource_rule_match(db_session, test_incident, test_alert):
    test_incident.correlation_key = f"resource_{test_alert.resource_id}"
    db_session.commit()
    
    engine = CorrelationEngine(db_session)
    result = engine.find_correlation(test_alert)
    
    assert result.incident is not None
    assert result.incident.id == test_incident.id
    assert result.reason == "SAME_RESOURCE"
    assert result.metadata["correlation_key"] == test_incident.correlation_key

def test_global_alert_rule_match(db_session, test_incident, test_alert):
    test_alert.resource_id = None
    test_incident.correlation_key = f"global_alert_{test_alert.integration_id}_{test_alert.alert_type}"
    db_session.commit()
    
    engine = CorrelationEngine(db_session)
    result = engine.find_correlation(test_alert)
    
    assert result.incident is not None
    assert result.incident.id == test_incident.id
    assert result.reason == "SAME_CORRELATION_KEY"
    assert result.metadata["correlation_key"] == test_incident.correlation_key

def test_no_match(db_session, test_alert):
    engine = CorrelationEngine(db_session)
    result = engine.find_correlation(test_alert)
    
    assert result.incident is None
    assert result.reason == "NO_MATCH"
    assert "correlation_key" in result.metadata
