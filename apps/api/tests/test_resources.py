import pytest


def test_create_resource(client_with_real_db, admin_token_headers, setup_environment):
    env_id = setup_environment["id"]
    response = client_with_real_db.post(
        "/api/v1/resources/",
        headers=admin_token_headers,
        json={
            "name": "web-server-01",
            "resource_type": "HOST",
            "provider": "manual",
            "environment_id": env_id,
            "status": "ACTIVE"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "web-server-01"
    assert data["resource_type"] == "HOST"
    assert data["status"] == "ACTIVE"


@pytest.fixture
def setup_environment(client_with_real_db, admin_token_headers):
    response = client_with_real_db.post(
        "/api/v1/environments/",
        headers=admin_token_headers,
        json={"name": "test-resource-env", "environment_type": "DEVELOPMENT"}
    )
    return response.json()


def test_duplicate_external_identity(client_with_real_db, admin_token_headers):
    # Nullable external_id allows duplicates if null
    client_with_real_db.post(
        "/api/v1/resources/",
        headers=admin_token_headers,
        json={"name": "res-1", "resource_type": "VM", "provider": "manual", "external_id": None}
    )
    client_with_real_db.post(
        "/api/v1/resources/",
        headers=admin_token_headers,
        json={"name": "res-2", "resource_type": "VM", "provider": "manual", "external_id": None}
    )

    # Not null external_id enforces unique constraint
    client_with_real_db.post(
        "/api/v1/resources/",
        headers=admin_token_headers,
        json={"name": "res-3", "resource_type": "VM", "provider": "manual", "external_id": "i-123"}
    )
    response = client_with_real_db.post(
        "/api/v1/resources/",
        headers=admin_token_headers,
        json={"name": "res-4", "resource_type": "VM", "provider": "manual", "external_id": "i-123"}
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["error"]["message"].lower()


def test_resource_filtering(client_with_real_db, admin_token_headers):
    client_with_real_db.post(
        "/api/v1/resources/",
        headers=admin_token_headers,
        json={"name": "filter-me-1", "resource_type": "DATABASE", "provider": "manual"}
    )
    client_with_real_db.post(
        "/api/v1/resources/",
        headers=admin_token_headers,
        json={"name": "filter-me-2", "resource_type": "STORAGE", "provider": "manual"}
    )

    response = client_with_real_db.get(
        "/api/v1/resources/?resource_type=DATABASE",
        headers=admin_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    assert all(item["resource_type"] == "DATABASE" for item in data["items"])


def test_resource_rbac(client_with_real_db, viewer_token_headers):
    response = client_with_real_db.post(
        "/api/v1/resources/",
        headers=viewer_token_headers,
        json={"name": "viewer-res", "resource_type": "VM", "provider": "manual"}
    )
    assert response.status_code == 403
