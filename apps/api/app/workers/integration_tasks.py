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
            
            # Automatically trigger discovery after successful validation
            discover_resources_task.delay(integration_id)
            
        except Exception as e:
            logger.error(f"Validation failed for integration {integration_id}: {str(e)}")
            service.update_status(UUID(integration_id), IntegrationStatus.UNHEALTHY)
            from app.integrations.exceptions import ProviderError
            if isinstance(e, ProviderError):
                logger.warning(f"Validation failed (ProviderError) for integration {integration_id}, retrying: {str(e)}")
                raise self.retry(exc=e, countdown=10)
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
            from app.integrations.exceptions import ProviderError
            if isinstance(e, ProviderError):
                logger.warning(f"Discovery failed (ProviderError) for integration {integration_id}, retrying: {str(e)}")
                raise self.retry(exc=e, countdown=15)
    finally:
        db.close()

@celery_app.task(bind=True, max_retries=3)
def poll_prometheus_alerts_task(self):
    logger.info("Starting Prometheus alert polling")
    SessionLocal = get_session_factory()
    db = SessionLocal()
    
    try:
        service = IntegrationService(db)
        from app.models.integration import Integration
        from app.models.enums import ProviderType
        
        # Get all healthy prometheus integrations
        integrations = db.query(Integration).filter(
            Integration.provider == ProviderType.PROMETHEUS.value,
            Integration.status == IntegrationStatus.HEALTHY
        ).all()
        
        from app.services.event_ingestion import EventIngestionService
        from app.schemas.events import RawEventCreate
        from datetime import datetime, timezone
        
        event_service = EventIngestionService(db)
        
        for integration in integrations:
            # Single-flight lock per integration using Redis
            lock_key = f"lock:prometheus_poll:{integration.id}"
            
            # Use raw redis client from celery/redis connection if available, 
            # or just rely on a simple DB-backed or Redis lock. 
            # Since Redis is our Celery broker, we can use celery_app.backend.client 
            # or just a simple try/except cache. 
            # We'll use a simple cache mechanism from redis
            import redis
            import os
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            try:
                r = redis.from_url(redis_url)
                if not r.set(lock_key, "1", nx=True, ex=50): # Lock for 50s
                    logger.info(f"Skipping poll for integration {integration.id}, lock is active.")
                    continue
            except Exception as lock_err:
                logger.warning(f"Failed to acquire redis lock: {str(lock_err)}")
                
            try:
                adapter = AdapterRegistry.get_adapter(integration.provider)
                secrets = decrypt_secret_payload(integration.secret_payload)
                
                alerts = adapter.get_alerts(integration.configuration, secrets)
                
                for alert in alerts:
                    labels = alert.get("labels", {})
                    alertname = labels.get("alertname", "UnknownAlert")
                    state = alert.get("state", "firing")
                    
                    # Generate deterministic event identity
                    external_event_id = f"{integration.id}-{alertname}-{labels.get('job', '')}-{labels.get('instance', '')}-{alert.get('activeAt', '')}"
                    
                    # Remove highly volatile fields like "value" to ensure payload hash idempotency
                    stable_payload = alert.copy()
                    if "value" in stable_payload:
                        del stable_payload["value"]
                    if "annotations" in stable_payload and "value" in stable_payload["annotations"]:
                        del stable_payload["annotations"]["value"]
                        
                    payload = stable_payload
                    occurred_at_str = alert.get("activeAt")
                    
                    try:
                        if occurred_at_str:
                            occurred_at = datetime.fromisoformat(occurred_at_str.replace("Z", "+00:00"))
                        else:
                            occurred_at = datetime.now(timezone.utc)
                    except ValueError:
                        occurred_at = datetime.now(timezone.utc)
                    
                    resource_external_id = None
                    if "job" in labels and "instance" in labels:
                        resource_external_id = f"{labels['job']}/{labels['instance']}"
                    
                    event_in = RawEventCreate(
                        provider=ProviderType.PROMETHEUS.value,
                        integration_id=integration.id,
                        external_event_id=external_event_id,
                        event_type=f"prometheus_{state}",
                        occurred_at=occurred_at,
                        resource_external_id=resource_external_id,
                        payload=payload
                    )
                    
                    # Ingest via existing event ingestion pipeline
                    # Use system user ID or none since it's an automated background task
                    event_service.ingest_event(event_in=event_in, current_user_id=None)
                    
            except Exception as e:
                logger.error(f"Failed to poll alerts for integration {integration.id}: {str(e)}")
                
    finally:
        db.close()

@celery_app.task(bind=True, max_retries=3)
def poll_nagios_status_task(self):
    logger.info("Starting Nagios status polling")
    SessionLocal = get_session_factory()
    db = SessionLocal()
    
    try:
        from app.models.integration import Integration
        from app.models.enums import ProviderType
        from app.services.event_ingestion import EventIngestionService
        from app.schemas.events import RawEventCreate
        from datetime import datetime, timezone
        import redis
        import os
        
        event_service = EventIngestionService(db)
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        integrations = db.query(Integration).filter(
            Integration.provider == ProviderType.NAGIOS.value,
            Integration.status == IntegrationStatus.HEALTHY
        ).all()
        
        for integration in integrations:
            lock_key = f"lock:nagios_poll:{integration.id}"
            
            try:
                r = redis.from_url(redis_url)
                if not r.set(lock_key, "1", nx=True, ex=50):
                    logger.info(f"Skipping poll for integration {integration.id}, lock is active.")
                    continue
            except Exception as lock_err:
                logger.warning(f"Failed to acquire redis lock: {str(lock_err)}")
                
            try:
                adapter = AdapterRegistry.get_adapter(integration.provider)
                secrets = decrypt_secret_payload(integration.secret_payload)
                
                # Fetch current status directly using the client from adapter
                client = adapter._get_client(integration.configuration, secrets)
                hosts, services = client.get_status()
                
                # Process Hosts
                for host in hosts:
                    if not host.host_name:
                        continue
                    
                    # Deterministic identity based on state changes to satisfy idempotency
                    external_event_id = f"{integration.id}-{host.host_name}-{host.current_state}-{host.last_state_change}"
                    
                    occurred_at = datetime.fromtimestamp(host.last_state_change, tz=timezone.utc) if host.last_state_change > 0 else datetime.now(timezone.utc)
                    resource_external_id = f"nagios/host/{host.host_name}"
                    
                    event_type = f"nagios_host_{host.current_state}"
                    payload = {
                        "host_name": host.host_name,
                        "current_state": host.current_state,
                        "last_state_change": host.last_state_change,
                        "acknowledged": bool(host.problem_has_been_acknowledged),
                        "plugin_output": host.plugin_output  # Safe as long as we anchor external_event_id
                    }
                    
                    event_in = RawEventCreate(
                        provider=ProviderType.NAGIOS.value,
                        integration_id=integration.id,
                        external_event_id=external_event_id,
                        event_type=event_type,
                        occurred_at=occurred_at,
                        resource_external_id=resource_external_id,
                        payload=payload
                    )
                    
                    event_service.ingest_event(event_in=event_in, current_user_id=None)
                    
                # Process Services
                for service in services:
                    if not service.host_name or not service.service_description:
                        continue
                        
                    external_event_id = f"{integration.id}-{service.host_name}-{service.service_description}-{service.current_state}-{service.last_state_change}"
                    
                    occurred_at = datetime.fromtimestamp(service.last_state_change, tz=timezone.utc) if service.last_state_change > 0 else datetime.now(timezone.utc)
                    resource_external_id = f"nagios/service/{service.host_name}/{service.service_description}"
                    
                    event_type = f"nagios_service_{service.current_state}"
                    payload = {
                        "host_name": service.host_name,
                        "service_description": service.service_description,
                        "current_state": service.current_state,
                        "last_state_change": service.last_state_change,
                        "acknowledged": bool(service.problem_has_been_acknowledged),
                        "plugin_output": service.plugin_output
                    }
                    
                    event_in = RawEventCreate(
                        provider=ProviderType.NAGIOS.value,
                        integration_id=integration.id,
                        external_event_id=external_event_id,
                        event_type=event_type,
                        occurred_at=occurred_at,
                        resource_external_id=resource_external_id,
                        payload=payload
                    )
                    
                    event_service.ingest_event(event_in=event_in, current_user_id=None)

            except Exception as e:
                logger.error(f"Failed to poll status for integration {integration.id}: {str(e)}")
                
    finally:
        db.close()
