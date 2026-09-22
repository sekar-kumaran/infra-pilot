import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.repositories import user as user_repo
from sqlalchemy import text
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

def register_user(db: Session, email: str, password: str) -> User:
    normalized_email = email.lower().strip()
    
    existing_user = user_repo.get_by_email(db, normalized_email)
    if existing_user:
        # Don't leak this normally in API, but service level can raise a specific error
        # Actually, standard practice is to raise 400 for existing email on register. 
        # The prompt says: "Duplicate registration safely rejected" 
        # And "Do not reveal whether an email exists" for invalid login attempts. For registration, 
        # revealing email exists is standard, but to be safe and strictly adhere to "Duplicate registration safely rejected"
        # we will raise a standard AuthException that the endpoint translates.
        raise AuthException("Email already registered")
        
    password_hash = get_password_hash(password)
    user = user_repo.create(db, email=normalized_email, password_hash=password_hash)
    
    # First-User Bootstrap (race-condition safe)
    # Lock an arbitrary high ID to serialize bootstrap logic across concurrent txns
    db.execute(text("SELECT pg_advisory_xact_lock(999999)"))
    admin_count = db.query(UserRole).join(Role).filter(Role.name == "ADMIN").count()
    
    if admin_count == 0:
        rbac_service.assign_role(db, user.id, "ADMIN")
    
    # Wait, we should also assign default roles if we have them, but for now we won't assign any 
    # to subsequent users as per instructions.
    
    audit_service.log_event(
        db=db,
        action="USER_REGISTERED",
        resource_type="USER",
        resource_id=str(user.id),
        result="SUCCESS",
        actor_user_id=user.id,
        metadata={"email": user.email}
    )
    
    return user

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    normalized_email = email.lower().strip()
    user = user_repo.get_by_email(db, normalized_email)
    
    if not user:
        # Audit log failed login (no actor since user not found)
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
