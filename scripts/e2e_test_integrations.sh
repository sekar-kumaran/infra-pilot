#!/bin/bash
set -e

echo "========================================="
echo " InfraPilot Phase 1.6 E2E Integration Test "
echo "========================================="

echo "1. Registering admin user..."
EMAIL="admin_$(date +%s)@example.com"
PASS="securepassword"
USER_RESP=$(curl -s -X POST "http://localhost:8000/api/v1/auth/register" -H "Content-Type: application/json" -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}")
USER_ID=$(echo $USER_RESP | grep -o '"id":"[^"]*' | grep -o '[^"]*$')

echo "Admin User ID: $USER_ID"

echo "2. Forcing admin role in database..."
docker exec infrapilot_postgres psql -U postgres -d infrapilot -c "INSERT INTO user_roles (id, user_id, role_id, created_at) SELECT gen_random_uuid(), '$USER_ID', id, NOW() FROM roles WHERE name = 'ADMIN';" > /dev/null

echo "3. Logging in as admin..."
LOGIN_RESP=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" -H "Content-Type: application/json" -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}")
TOKEN=$(echo $LOGIN_RESP | grep -o '"access_token":"[^"]*' | grep -o '[^"]*$')

echo "4. Creating Test Integration..."
CREATE_RESP=$(curl -s -X POST "http://localhost:8000/api/v1/integrations/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "E2E Test Integration",
    "provider": "TEST_PROVIDER",
    "description": "E2E automated testing integration",
    "configuration": {
      "test_mode": true,
      "test_token": "secret123"
    }
  }')

INTEGRATION_ID=$(echo $CREATE_RESP | grep -o '"id":"[^"]*' | grep -o '[^"]*$')
echo "Integration created: $INTEGRATION_ID"

echo "5. Triggering validation via Celery..."
curl -s -X POST "http://localhost:8000/api/v1/integrations/$INTEGRATION_ID/validate" \
  -H "Authorization: Bearer $TOKEN" > /dev/null

echo "Waiting for validation to complete..."
sleep 5

echo "6. Checking validation status..."
STATUS_RESP=$(curl -s -X GET "http://localhost:8000/api/v1/integrations/$INTEGRATION_ID" \
  -H "Authorization: Bearer $TOKEN")
STATUS=$(echo $STATUS_RESP | grep -o '"status":"[^"]*' | grep -o '[^"]*$')
echo "Integration Status: $STATUS"

if [ "$STATUS" == "HEALTHY" ]; then
    echo "SUCCESS: Validation completed successfully!"
else
    echo "ERROR: Validation failed, expected HEALTHY but got $STATUS"
    exit 1
fi

echo "7. Triggering discovery via Celery..."
curl -s -X POST "http://localhost:8000/api/v1/integrations/$INTEGRATION_ID/discover" \
  -H "Authorization: Bearer $TOKEN" > /dev/null

echo "Waiting for discovery to complete..."
sleep 5

echo "8. Checking discovered resources in DB..."
RESOURCES=$(docker exec infrapilot_postgres psql -U postgres -d infrapilot -t -c "SELECT COUNT(*) FROM infrastructure_resources WHERE provider = 'TEST_PROVIDER';")
echo "Discovered Resources: $RESOURCES"

if [ "$RESOURCES" -ge 2 ]; then
    echo "SUCCESS: Resources discovered successfully!"
else
    echo "ERROR: Discovery failed, expected >= 2 resources but got $RESOURCES"
    exit 1
fi

echo "========================================="
echo " ALL E2E TESTS PASSED                    "
echo "========================================="
