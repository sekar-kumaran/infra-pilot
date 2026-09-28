from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models.resource import InfrastructureResource
from app.models.enums import ResourceType
import logging

logger = logging.getLogger(__name__)

class ResourceCorrelator:
    """
    Correlates a target or incoming resource event into a canonical InfrastructureResource.
    This resolves cross-provider identities (e.g. Prometheus target -> AWS EC2 instance).
    """

    @classmethod
    def find_canonical_resource(
        cls, 
        db: Session, 
        attributes: Dict[str, Any]
    ) -> Optional[InfrastructureResource]:
        """
        Attempt to find exactly one matching resource based on safe deterministic attributes.
        Returns None if no match or multiple matches (fails safely).
        """
        query = db.query(InfrastructureResource).filter(InfrastructureResource.is_active == True)
        
        filters = []
        
        # 1. Exact canonical ID
        if "id" in attributes:
            return query.filter(InfrastructureResource.id == attributes["id"]).first()
            
        # 2. Provider specific external_id (e.g. aws/instance/i-12345)
        if "external_id" in attributes:
            filters.append(InfrastructureResource.external_id == attributes["external_id"])
            
        # 3. Safe identity attributes via JSONB metadata query
        if "instance_id" in attributes:
            filters.append(InfrastructureResource.metadata_["instance_id"].astext == attributes["instance_id"])
            
        if "container_id" in attributes:
            filters.append(InfrastructureResource.metadata_["container_id"].astext == attributes["container_id"])
            
        if "pod_name" in attributes:
            filters.append(InfrastructureResource.metadata_["pod_name"].astext == attributes["pod_name"])
            
        if "ip_address" in attributes:
            filters.append(InfrastructureResource.metadata_["private_ip"].astext == attributes["ip_address"])
            filters.append(InfrastructureResource.metadata_["public_ip"].astext == attributes["ip_address"])

        if not filters:
            return None
            
        # Try to find a match using OR so if any strong identifier matches, we get it
        results = query.filter(or_(*filters)).all()
        
        if len(results) == 1:
            return results[0]
            
        if len(results) > 1:
            logger.warning(f"Ambiguous resource match for attributes {attributes}. Found {len(results)} matches. Failing safely.")
            return None
            
        return None
