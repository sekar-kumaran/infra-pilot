def test_health_live(client):
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    # database field is omitted/null on liveness (no DB dependency)
    assert data.get("database") is None

def test_health_ready(client):
    response = client.get("/health/ready")
    # Ready returns 200 when DB is up, 503 when down.
    # Inside Docker the DB is always available, so expect 200.
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "healthy"
