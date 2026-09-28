from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user

router = APIRouter()

@router.get("/topology")
def get_topology(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from app.models.resource import InfrastructureResource
    resources = db.query(InfrastructureResource).all()
    
    nodes = []
    edges = []
    
    # We will just map resources to nodes
    for r in resources:
        nodes.append({
            "id": str(r.id),
            "label": r.name,
            "type": r.resource_type.lower() if r.resource_type else "server",
            "provider": r.provider
        })
        
    return {
        "nodes": nodes,
        "edges": edges
    }
