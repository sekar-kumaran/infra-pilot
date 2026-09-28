import pytest
from app.adapters.automation.ansible.executor import AnsibleAutomationExecutor
from app.adapters.automation.ansible.sanitizer import sanitize_identifier, redact_sensitive_data
from app.adapters.automation.ansible.errors import AnsibleValidationError

def test_sanitize_identifier_valid():
    assert sanitize_identifier("nginx") == "nginx"
    assert sanitize_identifier("my-service-name") == "my-service-name"
    assert sanitize_identifier("db_1.2") == "db_1.2"

def test_sanitize_identifier_invalid():
    with pytest.raises(ValueError):
        sanitize_identifier("nginx; rm -rf /")
    with pytest.raises(ValueError):
        sanitize_identifier("service && reboot")
    with pytest.raises(ValueError):
        sanitize_identifier("$(whoami)")
    with pytest.raises(ValueError):
        sanitize_identifier("nginx > /tmp/hacked")

def test_redact_sensitive_data():
    raw = "output containing password: my-secret-password and token=12345"
    safe = redact_sensitive_data(raw)
    assert "my-secret-password" not in safe
    assert "password: [REDACTED]" in safe
    assert "token: [REDACTED]" in safe
    assert "12345" not in safe
