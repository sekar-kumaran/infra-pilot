from typing import Optional
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.api.deps import get_current_user
from app.models.tenant import Tenant
from app.models.user import User

async def get_current_tenant(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Tenant:
    """
    Dependency to resolve the current tenant from the request context.
    Validates that the authenticated user belongs to the requested tenant.
    """
    tenant_header = request.headers.get("X-Tenant-ID")
    
    # If no specific tenant requested, use the user's default tenant
    tenant_id = tenant_header or current_user.tenant_id
    
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context is missing. Provide X-Tenant-ID header."
        )

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found."
        )
        
    if tenant.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant is not active."
        )
        
    # Enforce isolation: ensure user belongs to this tenant or is a global admin (if applicable)
    if current_user.tenant_id and str(current_user.tenant_id) != str(tenant.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to this tenant."
        )

    return tenant
