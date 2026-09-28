from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.auth import UserCreate
from app.services.auth import register_user, AuthException
from app.services.rbac import get_user_roles
from fastapi import HTTPException

router = APIRouter()

@router.post("")
def create_viewer_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    roles = get_user_roles(db, current_user.id)
    if "ADMIN" not in roles:
        raise HTTPException(status_code=403, detail="Only admins can create users")
    
    try:
        user = register_user(db, email=user_in.email, password=user_in.password, role="VIEWER")
        db.commit()
        return {"status": "success", "user_id": str(user.id)}
    except AuthException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=Dict[str, Any])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    users = db.query(User).offset(skip).limit(limit).all()
    total = db.query(User).count()
    
    return {
        "items": [
            {
                "id": str(user.id),
                "email": user.email,
                "name": getattr(user, 'name', None) or user.email.split('@')[0],
                "role": "Admin",  # Stubbed for now
                "status": "Active",
                "lastActive": "Just now"
            }
            for user in users
        ],
        "total": total,
        "page": (skip // limit) + 1,
        "size": limit
    }
