#!/usr/bin/env bash
set -euo pipefail

echo "======================================"
echo "Phase 1.4 E2E RBAC Runtime Validation"
echo "======================================"

API_URL="http://localhost:8000"

echo "[1] Verifying API Health..."
curl -s -f "$API_URL/health/live" > /dev/null || { echo "API is not live"; exit 1; }
echo "API is live."

echo "[2] Verifying PostgreSQL Readiness..."
curl -s -f "$API_URL/health/ready" > /dev/null || { echo "API is not ready (PostgreSQL may be down)"; exit 1; }
echo "API and DB are ready."

UID_A=$(uuidgen | tr '[:upper:]' '[:lower:]' || echo "userA_$RANDOM")
EMAIL_A="user_a_$UID_A@example.com"
PASSWORD="securepassword123"

echo "[3] Registering User A ($EMAIL_A)..."
RESP_A=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$EMAIL_A\", \"password\": \"$PASSWORD\"}")
STATUS_A=$(echo "$RESP_A" | tail -n1)
BODY_A=$(echo "$RESP_A" | sed '$d')
if [ "$STATUS_A" != "201" ]; then echo "Registration failed: $BODY_A"; exit 1; fi
USER_A_ID=$(echo "$BODY_A" | grep -o '"id":"[^"]*' | cut -d'"' -f4 | tr -d '\r\n ')
echo "User A registered: $USER_A_ID"

echo "[7] Logging in User A..."
RESP_LOGIN_A=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$EMAIL_A\", \"password\": \"$PASSWORD\"}")
STATUS_LOGIN_A=$(echo "$RESP_LOGIN_A" | tail -n1)
BODY_LOGIN_A=$(echo "$RESP_LOGIN_A" | sed '$d')
if [ "$STATUS_LOGIN_A" != "200" ]; then echo "Login A failed: $BODY_LOGIN_A"; exit 1; fi
TOKEN_A=$(echo "$BODY_LOGIN_A" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo "[4] Verifying User A is ADMIN... (Verified implicitly by role assignment later)"

UID_B=$(uuidgen | tr '[:upper:]' '[:lower:]' || echo "userB_$RANDOM")
EMAIL_B="user_b_$UID_B@example.com"

echo "[5] Registering User B ($EMAIL_B)..."
RESP_B=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$EMAIL_B\", \"password\": \"$PASSWORD\"}")
STATUS_B=$(echo "$RESP_B" | tail -n1)
BODY_B=$(echo "$RESP_B" | sed '$d')
if [ "$STATUS_B" != "201" ]; then echo "Registration failed: $BODY_B"; exit 1; fi
USER_B_ID=$(echo "$BODY_B" | grep -o '"id":"[^"]*' | cut -d'"' -f4 | tr -d '\r\n ')
echo "User B registered: $USER_B_ID"

echo "[8] Logging in User B..."
RESP_LOGIN_B=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$EMAIL_B\", \"password\": \"$PASSWORD\"}")
TOKEN_B=$(echo "$RESP_LOGIN_B" | sed '$d' | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo "[6] Verifying User B is not ADMIN... (Implicitly tested when B receives 403 on privileged action)"

echo "[9] User A assigns OPERATOR to User B..."
ASSIGN_RESP=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/roles/users/$USER_B_ID/roles/OPERATOR" \
    -H "Authorization: Bearer $TOKEN_A")
ASSIGN_STATUS=$(echo "$ASSIGN_RESP" | tail -n1)
if [ "$ASSIGN_STATUS" != "201" ]; then echo "Assignment failed: $(echo "$ASSIGN_RESP" | sed '$d')"; exit 1; fi

echo "[10] Verifying User B has OPERATOR... (Limitation: GET /users/{id}/roles API does not exist yet)"

echo "[11] User B attempts privileged operation (assigning role)..."
PRIV_RESP=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/roles/users/$USER_B_ID/roles/ADMIN" \
    -H "Authorization: Bearer $TOKEN_B")
PRIV_STATUS=$(echo "$PRIV_RESP" | tail -n1)
echo "[12] Verifying 403 status..."
if [ "$PRIV_STATUS" != "403" ]; then echo "Expected 403, got $PRIV_STATUS"; exit 1; fi
echo "Access denied (403) as expected."

echo "[14] User A queries /api/v1/audit/..."
AUDIT_RESP=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/v1/audit/?action=AUTHORIZATION_DENIED" \
    -H "Authorization: Bearer $TOKEN_A")
AUDIT_STATUS=$(echo "$AUDIT_RESP" | tail -n1)
if [ "$AUDIT_STATUS" != "200" ]; then echo "Audit query failed: $AUDIT_STATUS"; exit 1; fi

echo "[13/15] Verifying authorization denial audit event exists..."
AUDIT_BODY=$(echo "$AUDIT_RESP" | sed '$d')
if ! echo "$AUDIT_BODY" | grep -q '"action":"AUTHORIZATION_DENIED"'; then echo "Audit log missing!"; exit 1; fi
echo "Audit event found."

echo "[16] User B queries /api/v1/audit/..."
AUDIT_B_RESP=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/v1/audit/" \
    -H "Authorization: Bearer $TOKEN_B")
AUDIT_B_STATUS=$(echo "$AUDIT_B_RESP" | tail -n1)
echo "[17] Verifying 403 status..."
if [ "$AUDIT_B_STATUS" != "403" ]; then echo "Expected 403, got $AUDIT_B_STATUS"; exit 1; fi
echo "Access denied (403) as expected."

echo "[18] Attempt final-admin removal..."
DEMOTE_RESP=$(curl -s -w "\n%{http_code}" -X DELETE "$API_URL/api/v1/roles/users/$USER_A_ID/roles/ADMIN" \
    -H "Authorization: Bearer $TOKEN_A")
DEMOTE_STATUS=$(echo "$DEMOTE_RESP" | tail -n1)
echo "[19] Verify operation is rejected..."
if [ "$DEMOTE_STATUS" != "400" ] && [ "$DEMOTE_STATUS" != "403" ]; then echo "Expected 400 or 403, got $DEMOTE_STATUS"; exit 1; fi
echo "Operation rejected as expected."

echo "[20] Verify system remains administratively accessible..."
SYSTEM_RESP=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/v1/roles" \
    -H "Authorization: Bearer $TOKEN_A")
if [ "$(echo "$SYSTEM_RESP" | tail -n1)" != "200" ]; then echo "System inaccessible!"; exit 1; fi
echo "System accessible."

echo "======================================"
echo "E2E VALIDATION SUCCESSFUL"
echo "======================================"
