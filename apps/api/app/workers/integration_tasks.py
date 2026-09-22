import logging
from uuid import UUID

from celery import shared_task
from app.workers.celery_app import celery_app
from app.database.session import get_session_factory
from app.services.integrations import IntegrationService
from app.models.enums import IntegrationStatus
from app.integrations.registry import AdapterRegistry
from app.core.encryption import decrypt_secret_payload

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3)
def validate_integration_task(self, integration_id: str):
    logger.info(f"Starting validation for integration {integration_id}")
    SessionLocal = get_session_factory()
    db = SessionLocal()
    
    try:
        service = IntegrationService(db)
        integration = service.get(UUID(integration_id))
        
        if not integration:
            logger.error(f"Integration {integration_id} not found for validation")
            return
            
        service.update_status(UUID(integration_id), IntegrationStatus.VALIDATING)
        
        try:
            adapter = AdapterRegistry.get_adapter(integration.provider)
            secrets = decrypt_secret_payload(integration.secret_payload)
            
            # The adapter will raise an exception on failure
            adapter.validate_connection(integration.configuration, secrets)
            
            service.update_status(UUID(integration_id), IntegrationStatus.HEALTHY)
            logger.info(f"Integration {integration_id} validation successful")
            
        except Exception as e:
            logger.error(f"Validation failed for integration {integration_id}: {str(e)}")
            service.update_status(UUID(integration_id), IntegrationStatus.UNHEALTHY)
            # Depending on error type, we could retry
            # self.retry(exc=e, countdown=5)
            
    finally:
        db.close()

@celery_app.task(bind=True, max_retries=3)
def discover_resources_task(self, integration_id: str):
    logger.info(f"Starting discovery for integration {integration_id}")
    SessionLocal = get_session_factory()
    db = SessionLocal()
    
    try:
        service = IntegrationService(db)
        integration = service.get(UUID(integration_id))
        
        if not integration:
            logger.error(f"Integration {integration_id} not found for discovery")
            return
            
        if integration.status not in (IntegrationStatus.HEALTHY, IntegrationStatus.CONFIGURED):
            logger.warning(f"Skipping discovery for integration {integration_id} with status {integration.status}")
            return
            
        try:
            adapter = AdapterRegistry.get_adapter(integration.provider)
            secrets = decrypt_secret_payload(integration.secret_payload)
            
            discovered_resources = adapter.discover_resources(integration.configuration, secrets)
            logger.info(f"Discovered {len(discovered_resources)} resources from integration {integration_id}")
            
            # Synchronize into Phase 1.5 inventory
            service.synchronize_resources(UUID(integration_id), discovered_resources)
            
        except Exception as e:
            logger.error(f"Discovery failed for integration {integration_id}: {str(e)}")
            
    finally:
        db.close()
