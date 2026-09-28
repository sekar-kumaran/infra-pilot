#!/bin/sh

echo "==> Running database migrations..."
alembic upgrade heads

echo "==> Seeding default admin user..."
python -c "
from app.database.session import get_session_factory
from app.services.auth import register_user
db = get_session_factory()()
try:
    register_user(db, 'admin@infrapilot.com', 'Admin1234!')
    db.commit()
    print('Admin user created: admin@infrapilot.com / Admin1234!')
except Exception as e:
    db.rollback()
    print(f'Skipping seed (user may already exist): {e}')
finally:
    db.close()
"

echo "==> Starting InfraPilot API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
