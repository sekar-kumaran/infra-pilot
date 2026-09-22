from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.integration import Integration
from app.models.enums import IntegrationStatus
from app.schemas.integration import IntegrationCreate, IntegrationUpdate
from app.core.encryption import extract_secrets, encrypt_secret_payload, decrypt_secret_payload
from app.integrations.registry import AdapterRegistry
from app.integrations.models import IntegrationCapability, DiscoveredResource
from app.services.audit import log_event
from app.models.user import User
from app.repositories.resources import ResourceRepository
from app.schemas.inventory import InfrastructureResourceCreate, InfrastructureResourceUpdate
from app.models.enums import ResourceStatus

class IntegrationService:
    def __init__(self, db: Session):
        self.db = db

    def get(self, integration_id: UUID) -> Optional[Integration]:
        return self.db.query(Integration).filter(Integration.id == integration_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Integration]:
        return self.db.query(Integration).offset(skip).limit(limit).all()

    def create(self, integration_in: IntegrationCreate, current_user: User, request_id: str = None) -> Integration:
        # Extract secrets from configuration
        safe_config, extracted_secrets = extract_secrets(integration_in.configuration)
        
        # Encrypt the extracted secrets
        encrypted_payload = encrypt_secret_payload(extracted_secrets)
        
        # We also need to check if the adapter is registered
        # AdapterRegistry.get_adapter(integration_in.provider) # Will throw ProviderNotFoundError if unsupported

        integration = Integration(
            name=integration_in.name,
            provider=integration_in.provider.value,
            description=integration_in.description,
            configuration=safe_config,
            secret_payload=encrypted_payload,
            status=IntegrationStatus.CONFIGURED
        )
        
        self.db.add(integration)
        self.db.commit()
        self.db.refresh(integration)
        
        log_event(
            db=self.db,
            actor_user_id=current_user.id,
            action="integration.created",
            resource_type="integration",
            resource_id=str(integration.id),
            result="success",
            request_id=request_id,
            metadata={"name": integration.name, "provider": integration.provider.value if hasattr(integration.provider, 'value') else str(integration.provider)}
        )
        self.db.commit()
        
        return integration

    def update(self, integration: Integration, integration_in: IntegrationUpdate, current_user: User, request_id: str = None) -> Integration:
        update_data = integration_in.model_dump(exclude_unset=True)
        
        if "configuration" in update_data:
            # We need to merge secrets if they provided new ones, or replace entirely.
            # Usually, a PATCH configuration replaces or merges.
            # To keep it simple, we extract new secrets from the incoming config.
            safe_config, extracted_secrets = extract_secrets(update_data["configuration"])
            
            # Decrypt old secrets to merge with new ones
            existing_secrets = decrypt_secret_payload(integration.secret_payload)
            existing_secrets.update(extracted_secrets)
            
            integration.configuration = safe_config
            integration.secret_payload = encrypt_secret_payload(existing_secrets)
            del update_data["configuration"]
            
        for field, value in update_data.items():
            setattr(integration, field, value)
            
        self.db.commit()
        self.db.refresh(integration)
        
        log_event(
            db=self.db,
            actor_user_id=current_user.id,
            action="integration.updated",
            resource_type="integration",
            resource_id=str(integration.id),
            result="success",
            request_id=request_id,
            metadata={"name": integration.name}
        )
        self.db.commit()
        
        return integration

    def enable(self, integration: Integration, current_user: User, request_id: str = None) -> Integration:
        integration.status = IntegrationStatus.CONFIGURED
        self.db.commit()
        self.db.refresh(integration)
        
        log_event(
            db=self.db,
            actor_user_id=current_user.id,
            action="integration.enabled",
            resource_type="integration",
            resource_id=str(integration.id),
            result="success",
            request_id=request_id,
            metadata={}
        )
        self.db.commit()
        return integration

    def disable(self, integration: Integration, current_user: User, request_id: str = None) -> Integration:
        integration.status = IntegrationStatus.DISABLED
        self.db.commit()
        self.db.refresh(integration)
        
        log_event(
            db=self.db,
            actor_user_id=current_user.id,
            action="integration.disabled",
            resource_type="integration",
            resource_id=str(integration.id),
            result="success",
            request_id=request_id,
            metadata={}
        )
        self.db.commit()
        return integration

    def get_capabilities(self, integration: Integration) -> IntegrationCapability:
        adapter = AdapterRegistry.get_adapter(integration.provider)
        return adapter.get_capabilities()

    def update_status(self, integration_id: UUID, status: IntegrationStatus, request_id: str = None) -> Integration:
        integration = self.get(integration_id)
        if not integration:
            return None
        integration.status = status
        integration.last_checked_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(integration)
        return integration

    def synchronize_resources(self, integration_id: UUID, discovered_resources: List[DiscoveredResource]) -> None:
        integration = self.get(integration_id)
        if not integration:
            return
            
        resource_repo = ResourceRepository(self.db)
        
        for dr in discovered_resources:
            # Check if resource already exists
            existing = resource_repo.get_by_external_identity(dr.provider, dr.external_id)
            
            if existing:
                # Update
                update_schema = InfrastructureResourceUpdate(
                    name=dr.name,
                    display_name=dr.display_name,
                    status=dr.status,
                    description=dr.description,
                    metadata_=dr.metadata
                )
                resource_repo.update(existing, update_schema)
            else:
                # Create
                create_schema = InfrastructureResourceCreate(
                    provider=dr.provider,
                    external_id=dr.external_id,
                    name=dr.name,
                    display_name=dr.display_name,
                    resource_type=dr.resource_type,
                    status=dr.status,
                    description=dr.description,
                    metadata_=dr.metadata
                )
                resource_repo.create(create_schema)
                
        # Commit all sync changes
        self.db.commit()

