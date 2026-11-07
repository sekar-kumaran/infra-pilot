import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.repositories import user as user_repo
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User
from app.services import audit as audit_service
from app.services import rbac as rbac_service
from app.models.rbac import Role, UserRole

logger = logging.getLogger(__name__)

class AuthException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

def register_user(db: Session, email: str, password: str, role: Optional[str] = None) -> User:
    normalized_email = email.lower().strip()
    
    existing_user = user_repo.get_by_email(db, normalized_email)
    if existing_user:
        raise AuthException("Email already registered")
        
    password_hash = get_password_hash(password)
    user = user_repo.create(db, email=normalized_email, password_hash=password_hash)
    
    # Dialect-safe advisory lock for PostgreSQL
    try:
        bind = db.get_bind()
        if bind and bind.dialect.name == "postgresql":
            db.execute(text("SELECT pg_advisory_xact_lock(999999)"))
    except Exception:
        pass
        
    # First-user bootstrap: if no ADMIN user exists yet, first registered user becomes ADMIN; otherwise VIEWER
    if role is None:
        admin_role = db.query(Role).filter(Role.name == "ADMIN").first()
        admin_count = 0
        if admin_role:
            admin_count = db.query(UserRole).filter(UserRole.role_id == admin_role.id).count()
        target_role = "ADMIN" if admin_count == 0 else "VIEWER"
    else:
        target_role = role
        
    rbac_service.assign_role(db, user.id, target_role)
    
    audit_service.log_event(
        db=db,
        action="USER_REGISTERED",
        resource_type="USER",
        resource_id=str(user.id),
        result="SUCCESS",
        actor_user_id=user.id,
        metadata={"email": user.email, "assigned_role": target_role}
    )
    
    return user

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    normalized_email = email.lower().strip()
    user = user_repo.get_by_email(db, normalized_email)
    
    if not user:
        audit_service.log_event(
            db=db,
            action="USER_LOGIN_FAILED",
            resource_type="USER",
            result="FAILURE",
            metadata={"email": normalized_email, "reason": "user_not_found"}
        )
        return None
        
    if not verify_password(password, user.password_hash):
        audit_service.log_event(
            db=db,
            action="USER_LOGIN_FAILED",
            resource_type="USER",
            resource_id=str(user.id),
            result="FAILURE",
            actor_user_id=user.id,
            metadata={"email": normalized_email, "reason": "invalid_password"}
        )
        return None
        
    audit_service.log_event(
        db=db,
        action="USER_LOGIN_SUCCESS",
        resource_type="USER",
        resource_id=str(user.id),
        result="SUCCESS",
        actor_user_id=user.id,
        metadata={"email": normalized_email}
    )
        
    return user
