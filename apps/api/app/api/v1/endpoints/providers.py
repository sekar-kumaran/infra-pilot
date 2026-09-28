from typing import List, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.integrations.capabilities import ProviderCapabilityRegistry, ProviderCapabilityRegistryEntry

router = APIRouter()

@router.get("/capabilities", response_model=List[ProviderCapabilityRegistryEntry], dependencies=[Depends(require_permission("integrations:read"))])
def list_provider_capabilities(
    db: Session = Depends(get_db)
) -> Any:
    """
    Get the full registry of provider capabilities.
    """
    return ProviderCapabilityRegistry.get_all()
