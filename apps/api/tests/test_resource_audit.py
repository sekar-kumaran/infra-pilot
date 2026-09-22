import pytest


def test_audit_event_creation(client_with_real_db, admin_token_headers):
    # 1. Create a resource
    res = client_with_real_db.post(
        "/api/v1/resources/",
        headers=admin_token_headers,
        json={"name": "audit-test-res", "resource_type": "HOST", "provider": "manual"}
    )
    assert res.status_code == 201
    res_id = res.json()["id"]

    # 2. Check audit logs
    audit_res = client_with_real_db.get(
        f"/api/v1/audit/?resource_id={res_id}",
        headers=admin_token_headers
    )
    assert audit_res.status_code == 200
    events = audit_res.json()  # audit returns a list directly

    assert len(events) >= 1
    creation_event = next((e for e in events if e["action"] == "resource.created"), None)
    assert creation_event is not None
    assert creation_event["result"] == "success"


def test_metadata_security_rejection(client_with_real_db, admin_token_headers):
    # Metadata containing a password
    payload_1 = {
        "name": "bad-res-1",
        "resource_type": "VM",
        "provider": "manual",
        "metadata": {
            "password": "supersecretpassword123!"
        }
    }
    res1 = client_with_real_db.post(
        "/api/v1/resources/",
        headers=admin_token_headers,
        json=payload_1
    )
    assert res1.status_code == 400
    assert "sensitive key" in res1.json()["error"]["message"].lower()

    # Nested metadata containing a token
    payload_2 = {
        "name": "bad-res-2",
        "resource_type": "VM",
        "provider": "manual",
        "metadata": {
            "config": {
                "access_token": "ey12345"
            }
        }
    }
    res2 = client_with_real_db.post(
        "/api/v1/resources/",
        headers=admin_token_headers,
        json=payload_2
    )
    assert res2.status_code == 400
    assert "sensitive key" in res2.json()["error"]["message"].lower()

    # List nested metadata containing a JWT
    payload_3 = {
        "name": "bad-res-3",
        "resource_type": "VM",
        "provider": "manual",
        "metadata": {
            "auth_configs": [
                {"type": "basic"},
                {"type": "bearer", "jwt": "ey..."}
            ]
        }
    }
    res3 = client_with_real_db.post(
        "/api/v1/resources/",
        headers=admin_token_headers,
        json=payload_3
    )
    assert res3.status_code == 400
    assert "sensitive key" in res3.json()["error"]["message"].lower()
