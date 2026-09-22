from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User

def get_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def create(db: Session, email: str, password_hash: str) -> User:
    db_user = User(email=email, password_hash=password_hash)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
