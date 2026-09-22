from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
response = client.post(
    "/api/v1/auth/register",
    json={"email": "testclient@example.com", "password": "securepassword"}
)
print("Status Code:", response.status_code)
print("Response Text:", response.text)
