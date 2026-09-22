from typing import List, Tuple, Any, Dict, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.resource import InfrastructureResource
from app.models.resource_relationship import ResourceRelationship
from app.models.user import User
from app.schemas.inventory import (
    InfrastructureResourceCreate, 
    InfrastructureResourceUpdate,
    ResourceRelationshipCreate
)
from app.repositories.resources import ResourceRepository
from app.repositories.resource_relationships import ResourceRelationshipRepository
from app.repositories.environments import EnvironmentRepository
from app.services.audit import log_event
from app.models.enums import ResourceType, ProviderType, ResourceStatus, RelationshipType

SENSITIVE_KEYS = {
    "password", "password_hash", "token", "access_token", "refresh_token", 
    "jwt", "authorization", "secret", "api_key", "private_key", "database_url", 
    "auth_secret_key"
}

def validate_metadata(metadata: Dict[str, Any], path: str = "") -> None:
    if not isinstance(metadata, dict):
        return
    for k, v in metadata.items():
        if k.lower() in SENSITIVE_KEYS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sensitive key '{k}' found in metadata at {path or 'root'}. Persistence rejected."
            )
        if isinstance(v, dict):
            validate_metadata(v, f"{path}.{k}" if path else k)
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    validate_metadata(item, f"{path}.{k}[{i}]" if path else f"{k}[{i}]")


class ResourceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ResourceRepository(db)
        self.rel_repo = ResourceRelationshipRepository(db)
        self.env_repo = EnvironmentRepository(db)

    def _validate_environment(self, env_id: Optional[UUID]):
        if env_id is not None:
            if not self.env_repo.get_by_id(env_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Environment {env_id} not found"
                )

    def create_resource(self, resource_in: InfrastructureResourceCreate, current_user: User, request_id: str = None) -> InfrastructureResource:
        if resource_in.metadata:
            validate_metadata(resource_in.metadata)
            
        self._validate_environment(resource_in.environment_id)
        
        # Check uniqueness of provider + external_id if external_id is provided
        if resource_in.external_id is not None:
            existing = self.repo.get_by_external_identity(resource_in.provider, resource_in.external_id)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Resource with this provider and external_id already exists"
                )
                
        resource = self.repo.create(resource_in)
        
        log_event(
            db=self.db,
            actor_user_id=current_user.id,
            action="resource.created",
            resource_type="resource",
            resource_id=str(resource.id),
            result="success",
            request_id=request_id,
            metadata={"name": resource.name, "provider": resource.provider}
        )
        
        return resource

    def get_resource(self, resource_id: UUID) -> InfrastructureResource:
        resource = self.repo.get_by_id(resource_id)
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )
        return resource

    def list_resources(
        self, 
        page: int = 1, 
        page_size: int = 50,
        resource_type: Optional[ResourceType] = None,
        provider: Optional[ProviderType] = None,
        environment_id: Optional[UUID] = None,
        status: Optional[ResourceStatus] = None,
        name: Optional[str] = None,
        external_id: Optional[str] = None
    ) -> Tuple[List[InfrastructureResource], int]:
        return self.repo.list(
            page=page, page_size=page_size,
            resource_type=resource_type, provider=provider,
            environment_id=environment_id, status=status,
            name=name, external_id=external_id
        )

    def update_resource(self, resource_id: UUID, resource_in: InfrastructureResourceUpdate, current_user: User, request_id: str = None) -> InfrastructureResource:
        resource = self.get_resource(resource_id)
        
        if resource_in.metadata is not None:
            validate_metadata(resource_in.metadata)
            
        if resource_in.environment_id is not None and resource_in.environment_id != resource.environment_id:
            self._validate_environment(resource_in.environment_id)
            
        updated = self.repo.update(resource, resource_in)
        
        log_event(
            db=self.db,
            actor_user_id=current_user.id,
            action="resource.updated",
            resource_type="resource",
            resource_id=str(updated.id),
            result="success",
            request_id=request_id,
            metadata={"name": updated.name}
        )
        
        return updated

    def create_relationship(self, source_id: UUID, relationship_in: ResourceRelationshipCreate, current_user: User, request_id: str = None) -> ResourceRelationship:
        if relationship_in.metadata:
            validate_metadata(relationship_in.metadata)
            
        source = self.get_resource(source_id)
        target = self.get_resource(relationship_in.target_resource_id)
        
        if source.id == target.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Self-referencing relationships are not permitted"
            )
            
        if self.rel_repo.exists(source.id, target.id, relationship_in.relationship_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Relationship already exists"
            )
            
        rel = self.rel_repo.create(source.id, relationship_in)
        
        log_event(
            db=self.db,
            actor_user_id=current_user.id,
            action="relationship.created",
            resource_type="relationship",
            resource_id=str(rel.id),
            result="success",
            request_id=request_id,
            metadata={"source_id": str(source.id), "target_id": str(target.id), "type": rel.relationship_type}
        )
        
        return rel

    def list_relationships(self, resource_id: UUID, page: int = 1, page_size: int = 50) -> Tuple[List[ResourceRelationship], int]:
        # ensure resource exists
        self.get_resource(resource_id)
        return self.rel_repo.list_for_resource(resource_id, page=page, page_size=page_size)
