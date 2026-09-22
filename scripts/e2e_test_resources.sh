#!/bin/bash
set -e

API_URL="http://localhost:8000"

echo "========================================"
echo "Phase 1.5 E2E Resource Validation"
echo "========================================"

echo "[1] Verifying API Health..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health/live")
if [ "$HEALTH_STATUS" != "200" ]; then echo "API is down ($HEALTH_STATUS)"; exit 1; fi
echo "API is live."

echo "[2] Registering User and getting Admin token..."
ADMIN_EMAIL="admin_e2e_res_$RANDOM@example.com"
ADMIN_PW="SuperSecret123!"

# Register
REG_RESP=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$ADMIN_EMAIL\", \"password\": \"$ADMIN_PW\"}")
REG_STATUS=$(echo "$REG_RESP" | tail -n1)
if [ "$REG_STATUS" != "201" ]; then echo "Registration failed: $REG_STATUS"; exit 1; fi
ADMIN_ID=$(echo "$REG_RESP" | sed '$d' | grep -o '"id":"[^"]*' | cut -d'"' -f4)

# Login
LOGIN_RESP=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$ADMIN_EMAIL\", \"password\": \"$ADMIN_PW\"}")
TOKEN=$(echo "$LOGIN_RESP" | sed '$d' | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# We need to make this user an ADMIN directly via DB since only ADMIN can assign ADMIN
docker exec infrapilot_postgres psql -U postgres -d infrapilot -c "
INSERT INTO user_roles (id, user_id, role_id, created_at)
SELECT gen_random_uuid(), '$ADMIN_ID', id, now() FROM roles WHERE name='ADMIN';
" > /dev/null

echo "[3] Create Environment..."
ENV_RESP=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/environments/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"e2e-env-$(date +%s)\", \"environment_type\": \"DEVELOPMENT\"}")
ENV_STATUS=$(echo "$ENV_RESP" | tail -n1)
if [ "$ENV_STATUS" != "201" ]; then echo "Environment creation failed: $ENV_STATUS"; exit 1; fi
ENV_ID=$(echo "$ENV_RESP" | sed '$d' | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "Environment created: $ENV_ID"

echo "[4] Create Resource..."
RES1_RESP=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/resources/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"e2e-res-1\", \"resource_type\": \"HOST\", \"provider\": \"manual\", \"environment_id\": \"$ENV_ID\", \"status\": \"ACTIVE\"}")
RES1_STATUS=$(echo "$RES1_RESP" | tail -n1)
if [ "$RES1_STATUS" != "201" ]; then echo "Resource creation failed: $RES1_STATUS"; exit 1; fi
RES1_ID=$(echo "$RES1_RESP" | sed '$d' | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "Resource created: $RES1_ID"

echo "[5] Read Resource..."
GET_RESP=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/v1/resources/$RES1_ID" -H "Authorization: Bearer $TOKEN")
GET_STATUS=$(echo "$GET_RESP" | tail -n1)
if [ "$GET_STATUS" != "200" ]; then echo "Read resource failed: $GET_STATUS"; exit 1; fi

echo "[6] Filter Resources..."
FILT_RESP=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/v1/resources/?environment_id=$ENV_ID" -H "Authorization: Bearer $TOKEN")
FILT_STATUS=$(echo "$FILT_RESP" | tail -n1)
if [ "$FILT_STATUS" != "200" ]; then echo "Filter failed: $FILT_STATUS"; exit 1; fi

echo "[7] Update Resource..."
UPD_RESP=$(curl -s -w "\n%{http_code}" -X PATCH "$API_URL/api/v1/resources/$RES1_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"status\": \"MAINTENANCE\"}")
UPD_STATUS=$(echo "$UPD_RESP" | tail -n1)
if [ "$UPD_STATUS" != "200" ]; then echo "Update failed: $UPD_STATUS"; exit 1; fi

echo "[8] Create Second Resource..."
RES2_RESP=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/resources/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"e2e-res-2\", \"resource_type\": \"SERVICE\", \"provider\": \"manual\", \"environment_id\": \"$ENV_ID\"}")
RES2_ID=$(echo "$RES2_RESP" | sed '$d' | grep -o '"id":"[^"]*' | cut -d'"' -f4)

echo "[9] Create Relationship..."
REL_RESP=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/resources/$RES1_ID/relationships" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"target_resource_id\": \"$RES2_ID\", \"relationship_type\": \"HOSTS\"}")
REL_STATUS=$(echo "$REL_RESP" | tail -n1)
if [ "$REL_STATUS" != "201" ]; then echo "Relationship creation failed: $REL_STATUS"; exit 1; fi

echo "[10] Read Relationship..."
LREL_RESP=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/v1/resources/$RES1_ID/relationships" -H "Authorization: Bearer $TOKEN")
LREL_STATUS=$(echo "$LREL_RESP" | tail -n1)
if [ "$LREL_STATUS" != "200" ]; then echo "Read relationships failed: $LREL_STATUS"; exit 1; fi

echo "[11] Attempt Unauthorized Operation..."
# Create a user without permissions
VIEWER_EMAIL="viewer_e2e_$RANDOM@example.com"
curl -s -X POST "$API_URL/api/v1/auth/register" -H "Content-Type: application/json" -d "{\"email\": \"$VIEWER_EMAIL\", \"password\": \"$ADMIN_PW\"}" > /dev/null
VLOGIN_RESP=$(curl -s -X POST "$API_URL/api/v1/auth/login" -H "Content-Type: application/json" -d "{\"email\": \"$VIEWER_EMAIL\", \"password\": \"$ADMIN_PW\"}")
V_TOKEN=$(echo "$VLOGIN_RESP" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

UNAUTH_RESP=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/resources/" \
    -H "Authorization: Bearer $V_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"bad\", \"resource_type\": \"HOST\", \"provider\": \"manual\"}")
UNAUTH_STATUS=$(echo "$UNAUTH_RESP" | tail -n1)

echo "[12] Verify 403..."
if [ "$UNAUTH_STATUS" != "403" ]; then echo "Expected 403, got $UNAUTH_STATUS"; exit 1; fi

echo "[13] Query audit API..."
AUDIT_RESP=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/v1/audit/?resource_id=$RES1_ID" -H "Authorization: Bearer $TOKEN")
AUDIT_STATUS=$(echo "$AUDIT_RESP" | tail -n1)
if [ "$AUDIT_STATUS" != "200" ]; then echo "Audit query failed: $AUDIT_STATUS"; exit 1; fi

echo "[14] Verify resource audit events..."
AUDIT_BODY=$(echo "$AUDIT_RESP" | sed '$d')
if ! echo "$AUDIT_BODY" | grep -q '"action":"resource.created"'; then echo "Resource audit not found"; exit 1; fi
echo "Resource audit event found."

echo "[15] Verify environment audit events..."
ENV_AUDIT_RESP=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/v1/audit/?resource_id=$ENV_ID" -H "Authorization: Bearer $TOKEN")
if ! echo "$ENV_AUDIT_RESP" | sed '$d' | grep -q '"action":"environment.created"'; then echo "Environment audit not found"; exit 1; fi
echo "Environment audit event found."

echo "========================================"
echo "E2E RESOURCE VALIDATION SUCCESSFUL"
echo "========================================"
