import pytest
import uuid
from app.models.enums import ProviderType, IntegrationStatus
from app.services.rbac import assign_role



def test_create_integration(client_with_real_db, admin_token_headers):
    payload = {
        "name": "Test Integration",
        "provider": ProviderType.TEST_PROVIDER.value,
        "description": "A test integration",
        "configuration": {
            "test_mode": True,
            "test_token": "valid"
        }
    }
    
    response = client_with_real_db.post("/api/v1/integrations/", json=payload, headers=admin_token_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Integration"
    assert "test_token" not in data["configuration"]
    assert data["status"] == IntegrationStatus.CONFIGURED.value

def test_get_capabilities(client_with_real_db, admin_token_headers):
    payload = {
        "name": "Test Integration 2",
        "provider": ProviderType.TEST_PROVIDER.value,
        "configuration": {}
    }
    
    res = client_with_real_db.post("/api/v1/integrations/", json=payload, headers=admin_token_headers)
    assert res.status_code == 201
    integration_id = res.json()["id"]
    
    res2 = client_with_real_db.get(f"/api/v1/integrations/{integration_id}/capabilities", headers=admin_token_headers)
    assert res2.status_code == 200
    caps = res2.json()["capabilities"]
    assert caps["resource_discovery"] is True
    assert caps["health_check"] is True

def test_unauthorized_access(client_with_real_db):
    response = client_with_real_db.get("/api/v1/integrations/")
    assert response.status_code == 403
