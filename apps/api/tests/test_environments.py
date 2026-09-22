import pytest


def test_create_environment(client_with_real_db, admin_token_headers):
    response = client_with_real_db.post(
        "/api/v1/environments/",
        headers=admin_token_headers,
        json={
            "name": "prod-us-east-1",
            "description": "Production environment in US East",
            "environment_type": "PRODUCTION"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "prod-us-east-1"
    assert data["environment_type"] == "PRODUCTION"
    assert "id" in data


def test_create_duplicate_environment(client_with_real_db, admin_token_headers):
    client_with_real_db.post(
        "/api/v1/environments/",
        headers=admin_token_headers,
        json={"name": "test-env-dup", "environment_type": "DEVELOPMENT"}
    )
    # Duplicate
    response = client_with_real_db.post(
        "/api/v1/environments/",
        headers=admin_token_headers,
        json={"name": "test-env-dup", "environment_type": "STAGING"}
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["error"]["message"].lower()


def test_read_environment(client_with_real_db, admin_token_headers, operator_token_headers):
    create_resp = client_with_real_db.post(
        "/api/v1/environments/",
        headers=admin_token_headers,
        json={"name": "read-test-env", "environment_type": "STAGING"}
    )
    env_id = create_resp.json()["id"]

    # Read as Operator
    response = client_with_real_db.get(
        f"/api/v1/environments/{env_id}",
        headers=operator_token_headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "read-test-env"


def test_update_environment(client_with_real_db, admin_token_headers):
    create_resp = client_with_real_db.post(
        "/api/v1/environments/",
        headers=admin_token_headers,
        json={"name": "update-test-env", "environment_type": "STAGING"}
    )
    env_id = create_resp.json()["id"]

    response = client_with_real_db.patch(
        f"/api/v1/environments/{env_id}",
        headers=admin_token_headers,
        json={"description": "Updated desc"}
    )
    assert response.status_code == 200
    assert response.json()["description"] == "Updated desc"
    assert response.json()["name"] == "update-test-env"


def test_rbac_environment_create(client_with_real_db, viewer_token_headers):
    # Viewer does not have environments:create
    response = client_with_real_db.post(
        "/api/v1/environments/",
        headers=viewer_token_headers,
        json={"name": "viewer-env", "environment_type": "DEVELOPMENT"}
    )
    assert response.status_code == 403
