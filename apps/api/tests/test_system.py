def test_system_info(client):
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    data = response.json()
    assert "application_name" in data
    assert "version" in data
    assert "environment" in data
    # Ensure no secrets leak
    assert "DATABASE_URL" not in data
