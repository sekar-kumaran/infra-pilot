from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from app.models.rbac import Role, Permission, UserRole, RolePermission

def get_role_by_name(db: Session, name: str) -> Optional[Role]:
    return db.query(Role).filter(Role.name == name).first()

def get_role_by_id(db: Session, role_id: UUID) -> Optional[Role]:
    return db.query(Role).filter(Role.id == role_id).first()

def get_roles(db: Session) -> List[Role]:
    return db.query(Role).all()

def get_user_roles(db: Session, user_id: UUID) -> List[Role]:
    user_roles = db.query(UserRole).options(joinedload(UserRole.role)).filter(UserRole.user_id == user_id).all()
    return [ur.role for ur in user_roles]

def get_user_permissions(db: Session, user_id: UUID) -> List[str]:
    ur_list = db.query(UserRole).filter(UserRole.user_id == user_id).all()
    role_ids = [ur.role_id for ur in ur_list]
    if not role_ids:
        return []
        
    rp_list = db.query(RolePermission).filter(RolePermission.role_id.in_(role_ids)).all()
    perm_ids = [rp.permission_id for rp in rp_list]
    if not perm_ids:
        return []
        
    permissions = db.query(Permission.name).filter(Permission.id.in_(perm_ids)).distinct().all()
    return [p[0] for p in permissions]

def assign_role_to_user(db: Session, user_id: UUID, role_id: UUID) -> UserRole:
    ur = UserRole(user_id=user_id, role_id=role_id)
    db.add(ur)
    db.flush()
    return ur

def remove_role_from_user(db: Session, user_id: UUID, role_id: UUID) -> bool:
    deleted = db.query(UserRole).filter(UserRole.user_id == user_id, UserRole.role_id == role_id).delete()
    db.flush()
    return deleted > 0

def get_user_role_by_role_id(db: Session, user_id: UUID, role_id: UUID) -> Optional[UserRole]:
    return db.query(UserRole).filter(UserRole.user_id == user_id, UserRole.role_id == role_id).first()

def count_users_with_role(db: Session, role_id: UUID) -> int:
    return db.query(UserRole).filter(UserRole.role_id == role_id).count()
