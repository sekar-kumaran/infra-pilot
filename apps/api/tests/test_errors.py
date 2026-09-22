def test_404_error(client):
    response = client.get("/api/v1/invalid_path")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "HTTP_ERROR"
    assert "request_id" in data["error"]

def test_validation_error(client):
    # We don't have a POST endpoint yet to test payload validation easily,
    # but the handler is registered.
    pass
