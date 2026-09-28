import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.integration import Integration

logger = logging.getLogger(__name__)

class CircuitBreakerService:
    def __init__(self, db: Session):
        self.db = db
        self.failure_threshold = 5
        self.half_open_timeout_seconds = 60

    def is_available(self, provider_name: str, tenant_id: UUID) -> bool:
        """
        Check if the provider circuit breaker is allowing requests.
        """
        integration = self.db.query(Integration).filter(
            Integration.provider == provider_name,
            Integration.tenant_id == tenant_id
        ).first()
        
        if not integration:
            # If no integration is configured, we can't break the circuit on it, but it might just fail normally.
            return True

        if integration.circuit_state == "CLOSED":
            return True
            
        if integration.circuit_state == "OPEN":
            # Check if it's time to transition to HALF_OPEN
            if integration.last_failure_at:
                now = datetime.now(timezone.utc)
                if now - integration.last_failure_at > timedelta(seconds=self.half_open_timeout_seconds):
                    integration.circuit_state = "HALF_OPEN"
                    self.db.commit()
                    logger.info(f"Circuit breaker for {provider_name} transitioned to HALF_OPEN")
                    return True
            return False
            
        if integration.circuit_state == "HALF_OPEN":
            # Only allow one test request (simplistic approach: we let it through, 
            # if it fails it opens again, if it succeeds it closes)
            return True
            
        return True

    def record_success(self, provider_name: str, tenant_id: UUID):
        """
        Record a successful interaction, closing the circuit if it was open.
        """
        integration = self.db.query(Integration).filter(
            Integration.provider == provider_name,
            Integration.tenant_id == tenant_id
        ).first()
        
        if integration and (integration.failure_count > 0 or integration.circuit_state != "CLOSED"):
            integration.failure_count = 0
            integration.circuit_state = "CLOSED"
            self.db.commit()
            logger.info(f"Circuit breaker for {provider_name} transitioned to CLOSED (success)")

    def record_failure(self, provider_name: str, tenant_id: UUID):
        """
        Record a failed interaction, opening the circuit if threshold is reached.
        """
        integration = self.db.query(Integration).filter(
            Integration.provider == provider_name,
            Integration.tenant_id == tenant_id
        ).first()
        
        if integration:
            integration.failure_count += 1
            integration.last_failure_at = datetime.now(timezone.utc)
            
            if integration.circuit_state == "HALF_OPEN":
                integration.circuit_state = "OPEN"
                logger.warning(f"Circuit breaker for {provider_name} transitioned to OPEN (failed in HALF_OPEN)")
            elif integration.failure_count >= self.failure_threshold:
                if integration.circuit_state != "OPEN":
                    integration.circuit_state = "OPEN"
                    logger.warning(f"Circuit breaker for {provider_name} transitioned to OPEN (threshold reached)")
                    
            self.db.commit()
