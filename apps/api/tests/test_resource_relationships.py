import pytest


@pytest.fixture
def setup_resources(client_with_real_db, admin_token_headers):
    res1 = client_with_real_db.post(
        "/api/v1/resources/",
        headers=admin_token_headers,
        json={"name": "source-res", "resource_type": "HOST", "provider": "manual"}
    )
    res2 = client_with_real_db.post(
        "/api/v1/resources/",
        headers=admin_token_headers,
        json={"name": "target-res", "resource_type": "CONTAINER", "provider": "manual"}
    )
    return res1.json(), res2.json()


def test_create_relationship(client_with_real_db, admin_token_headers, setup_resources):
    res1, res2 = setup_resources

    response = client_with_real_db.post(
        f"/api/v1/resources/{res1['id']}/relationships",
        headers=admin_token_headers,
        json={
            "target_resource_id": res2["id"],
            "relationship_type": "CONTAINS"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["source_resource_id"] == res1["id"]
    assert data["target_resource_id"] == res2["id"]
    assert data["relationship_type"] == "CONTAINS"


def test_duplicate_relationship(client_with_real_db, admin_token_headers, setup_resources):
    res1, res2 = setup_resources

    client_with_real_db.post(
        f"/api/v1/resources/{res1['id']}/relationships",
        headers=admin_token_headers,
        json={"target_resource_id": res2["id"], "relationship_type": "DEPENDS_ON"}
    )

    response = client_with_real_db.post(
        f"/api/v1/resources/{res1['id']}/relationships",
        headers=admin_token_headers,
        json={"target_resource_id": res2["id"], "relationship_type": "DEPENDS_ON"}
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["error"]["message"].lower()


def test_self_reference(client_with_real_db, admin_token_headers, setup_resources):
    res1, _ = setup_resources

    response = client_with_real_db.post(
        f"/api/v1/resources/{res1['id']}/relationships",
        headers=admin_token_headers,
        json={"target_resource_id": res1["id"], "relationship_type": "DEPENDS_ON"}
    )
    assert response.status_code == 400
    assert "self-referencing" in response.json()["error"]["message"].lower()
