import httpx
resp = httpx.post('http://localhost:8000/api/v1/auth/register', json={'email': 'newuser888@example.com', 'password': 'securepassword'})
print(resp.status_code)
print(resp.json())
