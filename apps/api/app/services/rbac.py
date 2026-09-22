from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.repositories import rbac as rbac_repo
from app.repositories import user as user_repo

class RBACException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

def get_user_permissions(db: Session, user_id: UUID) -> List[str]:
    return rbac_repo.get_user_permissions(db, user_id)

def get_user_roles(db: Session, user_id: UUID) -> List[str]:
    roles = rbac_repo.get_user_roles(db, user_id)
    return [r.name for r in roles]

def get_roles(db: Session):
    return rbac_repo.get_roles(db)

def assign_role(db: Session, user_id: UUID, role_name: str) -> bool:
    role = rbac_repo.get_role_by_name(db, role_name)
    if not role:
        raise RBACException(f"Role {role_name} not found")
        
    user = user_repo.get_by_email(db, str(user_id)) # We don't have get_by_id yet, let's fix user_repo soon
    # Wait, we can just do a query here or update user_repo.
    # Let's assume user_repo.get_by_id will be implemented
    user = db.query(user_repo.User).filter(user_repo.User.id == user_id).first()
    if not user:
        raise RBACException("User not found")
        
    existing = rbac_repo.get_user_role_by_role_id(db, user_id, role.id)
    if existing:
        return False # Already assigned
        
    rbac_repo.assign_role_to_user(db, user_id, role.id)
    return True

def remove_role(db: Session, user_id: UUID, role_name: str) -> bool:
    role = rbac_repo.get_role_by_name(db, role_name)
    if not role:
        raise RBACException(f"Role {role_name} not found")
        
    # Last admin protection
    if role_name == "ADMIN":
        count = rbac_repo.count_users_with_role(db, role.id)
        if count <= 1:
            existing = rbac_repo.get_user_role_by_role_id(db, user_id, role.id)
            if existing:
                raise RBACException("Cannot remove the last ADMIN role")
                
    removed = rbac_repo.remove_role_from_user(db, user_id, role.id)
    return removed
