from typing import List, Tuple, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, func, exc

from app.models.resource_relationship import ResourceRelationship
from app.schemas.inventory import ResourceRelationshipCreate
from app.models.enums import RelationshipType

class ResourceRelationshipRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, source_id: UUID, relationship_in: ResourceRelationshipCreate) -> ResourceRelationship:
        data = relationship_in.model_dump()
        if 'metadata' in data:
            data['metadata_'] = data.pop('metadata')
            
        data['source_resource_id'] = source_id
        
        relationship = ResourceRelationship(**data)
        self.db.add(relationship)
        try:
            self.db.flush()
            return relationship
        except exc.IntegrityError:
            self.db.rollback()
            raise ValueError("Relationship already exists or violates constraints")

    def get_by_id(self, relationship_id: UUID) -> Optional[ResourceRelationship]:
        return self.db.execute(
            select(ResourceRelationship).where(ResourceRelationship.id == relationship_id)
        ).scalar_one_or_none()

    def list_for_resource(
        self, 
        resource_id: UUID, 
        page: int = 1, 
        page_size: int = 50
    ) -> Tuple[List[ResourceRelationship], int]:
        
        query = select(ResourceRelationship).where(
            (ResourceRelationship.source_resource_id == resource_id) | 
            (ResourceRelationship.target_resource_id == resource_id)
        )
        
        count_query = select(func.count(ResourceRelationship.id)).where(
            (ResourceRelationship.source_resource_id == resource_id) | 
            (ResourceRelationship.target_resource_id == resource_id)
        )
        
        total = self.db.execute(count_query).scalar_one()
        
        offset = (page - 1) * page_size
        items = self.db.execute(
            query.order_by(ResourceRelationship.created_at.desc())
            .offset(offset)
            .limit(page_size)
        ).scalars().all()
        
        return list(items), total

    def exists(self, source_id: UUID, target_id: UUID, rel_type: RelationshipType) -> bool:
        return self.db.execute(
            select(ResourceRelationship)
            .where(ResourceRelationship.source_resource_id == source_id)
            .where(ResourceRelationship.target_resource_id == target_id)
            .where(ResourceRelationship.relationship_type == rel_type)
        ).scalar_one_or_none() is not None
