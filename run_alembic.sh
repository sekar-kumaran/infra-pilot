#!/bin/sh
# Run inside the API container to execute alembic commands
export DATABASE_URL="postgresql+psycopg2://postgres:postgrespassword@postgres:5432/infrapilot"
cd /app
echo "=== alembic current ==="
alembic -c /app/alembic.ini current
echo "=== alembic history ==="
alembic -c /app/alembic.ini history
echo "=== alembic upgrade head ==="
alembic -c /app/alembic.ini upgrade head
echo "=== alembic current (after upgrade) ==="
alembic -c /app/alembic.ini current
