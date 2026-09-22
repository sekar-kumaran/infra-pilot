from app.database.session import get_session_factory
from app.services.integrations import IntegrationService
from app.schemas.integration import IntegrationCreate
from app.models.enums import ProviderType
from app.models.user import User
from sqlalchemy import text
import uuid

db = get_session_factory()()
user = db.query(User).first()
if not user:
    print('No user')
    exit(1)

svc = IntegrationService(db)
try:
    inc = IntegrationCreate(name='test_audit', provider=ProviderType.TEST, description='x', configuration={'host':'a'})
    svc.create(integration_in=inc, current_user=user)
    print('Created successfully')
except Exception as e:
    print('Error:', e)

events = db.execute(text("SELECT action FROM audit_events WHERE resource_type='integration'")).fetchall()
print('Integration events:', events)
