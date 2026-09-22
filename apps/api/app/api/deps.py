import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.config import settings
from app.database.session import get_db
from app.models.user import User

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.AUTH_SECRET_KEY, algorithms=[settings.AUTH_ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = UUID(user_id_str)
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception
        
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
        
        
    return user

def require_permission(required_permission: str):
    def permission_dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        from app.services.rbac import get_user_permissions
        from app.services.audit import log_event
        from app.database.session import get_session_factory
        
        permissions = get_user_permissions(db, current_user.id)
        if required_permission not in permissions:
            log_event(
                db=db,
                action="AUTHORIZATION_DENIED",
                resource_type="PERMISSION",
                resource_id=required_permission,
                result="DENY",
                actor_user_id=current_user.id,
                metadata={"reason": "missing_permission"}
            )
            db.commit()
            
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
            
        return current_user
    return permission_dependency
