import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.rbac import RoleResponse
from app.services import rbac as rbac_service
from app.services import audit as audit_service
from app.api.deps import require_permission

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("", response_model=list[RoleResponse])
def get_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("roles:read"))
):
    """
    List all available roles.
    """
    return rbac_service.get_roles(db)

@router.post("/users/{user_id}/roles/{role_name}", status_code=status.HTTP_201_CREATED)
def assign_role_to_user(
    user_id: UUID,
    role_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("roles:manage"))
):
    """
    Assign a role to a user.
    """
    if current_user.id == user_id:
        audit_service.log_event(
            db=db,
            action="ROLE_ASSIGNED",
            resource_type="USER_ROLE",
            result="DENY",
            actor_user_id=current_user.id,
            metadata={"reason": "self_escalation_attempt", "target_user_id": str(user_id), "role_name": role_name}
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot assign roles to yourself")
        
    try:
        assigned = rbac_service.assign_role(db, user_id, role_name)
        if assigned:
            audit_service.log_event(
                db=db,
                action="ROLE_ASSIGNED",
                resource_type="USER_ROLE",
                result="SUCCESS",
                actor_user_id=current_user.id,
                metadata={"target_user_id": str(user_id), "role_name": role_name}
            )
        return {"detail": "Role assigned successfully"}
    except rbac_service.RBACException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/users/{user_id}/roles/{role_name}", status_code=status.HTTP_200_OK)
def remove_role_from_user(
    user_id: UUID,
    role_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("roles:manage"))
):
    """
    Remove a role from a user.
    """
    if current_user.id == user_id:
        audit_service.log_event(
            db=db,
            action="ROLE_REMOVED",
            resource_type="USER_ROLE",
            result="DENY",
            actor_user_id=current_user.id,
            metadata={"reason": "self_demotion_attempt", "target_user_id": str(user_id), "role_name": role_name}
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot remove roles from yourself")
        
    try:
        removed = rbac_service.remove_role(db, user_id, role_name)
        if removed:
            audit_service.log_event(
                db=db,
                action="ROLE_REMOVED",
                resource_type="USER_ROLE",
                result="SUCCESS",
                actor_user_id=current_user.id,
                metadata={"target_user_id": str(user_id), "role_name": role_name}
            )
        return {"detail": "Role removed successfully"}
    except rbac_service.RBACException as e:
        audit_service.log_event(
            db=db,
            action="ROLE_REMOVED",
            resource_type="USER_ROLE",
            result="DENY",
            actor_user_id=current_user.id,
            metadata={"reason": str(e), "target_user_id": str(user_id), "role_name": role_name}
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
