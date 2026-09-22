from typing import List, Tuple, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, func, exc

from app.models.resource import InfrastructureResource
from app.schemas.inventory import InfrastructureResourceCreate, InfrastructureResourceUpdate
from app.models.enums import ResourceType, ProviderType, ResourceStatus

class ResourceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, resource_in: InfrastructureResourceCreate) -> InfrastructureResource:
        # Pydantic's 'metadata' alias maps to 'metadata_' in SQLAlchemy
        data = resource_in.model_dump()
        if 'metadata' in data:
            data['metadata_'] = data.pop('metadata')
            
        resource = InfrastructureResource(**data)
        self.db.add(resource)
        try:
            self.db.flush()
            return resource
        except exc.IntegrityError:
            self.db.rollback()
            raise ValueError("Resource with this provider and external_id already exists")

    def get_by_id(self, resource_id: UUID) -> Optional[InfrastructureResource]:
        return self.db.execute(
            select(InfrastructureResource).where(InfrastructureResource.id == resource_id)
        ).scalar_one_or_none()

    def get_by_external_identity(self, provider: str, external_id: str) -> Optional[InfrastructureResource]:
        return self.db.execute(
            select(InfrastructureResource)
            .where(InfrastructureResource.provider == provider)
            .where(InfrastructureResource.external_id == external_id)
        ).scalar_one_or_none()

    def list(
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
        
        query = select(InfrastructureResource)
        count_query = select(func.count(InfrastructureResource.id))
        
        # Apply filters
        if resource_type:
            query = query.where(InfrastructureResource.resource_type == resource_type)
            count_query = count_query.where(InfrastructureResource.resource_type == resource_type)
        if provider:
            query = query.where(InfrastructureResource.provider == provider)
            count_query = count_query.where(InfrastructureResource.provider == provider)
        if environment_id:
            query = query.where(InfrastructureResource.environment_id == environment_id)
            count_query = count_query.where(InfrastructureResource.environment_id == environment_id)
        if status:
            query = query.where(InfrastructureResource.status == status)
            count_query = count_query.where(InfrastructureResource.status == status)
        if name:
            query = query.where(InfrastructureResource.name.ilike(f"%{name}%"))
            count_query = count_query.where(InfrastructureResource.name.ilike(f"%{name}%"))
        if external_id:
            query = query.where(InfrastructureResource.external_id == external_id)
            count_query = count_query.where(InfrastructureResource.external_id == external_id)

        total = self.db.execute(count_query).scalar_one()
        
        offset = (page - 1) * page_size
        items = self.db.execute(
            query.order_by(InfrastructureResource.created_at.desc())
            .offset(offset)
            .limit(page_size)
        ).scalars().all()
        
        return list(items), total

    def update(self, resource: InfrastructureResource, resource_in: InfrastructureResourceUpdate) -> InfrastructureResource:
        update_data = resource_in.model_dump(exclude_unset=True)
        if 'metadata' in update_data:
            update_data['metadata_'] = update_data.pop('metadata')
            
        for field, value in update_data.items():
            setattr(resource, field, value)
        try:
            self.db.flush()
            return resource
        except exc.IntegrityError:
            self.db.rollback()
            raise ValueError("Update violates unique constraints")
