from typing import List, Tuple, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, func, exc

from app.models.environment import Environment
from app.schemas.inventory import EnvironmentCreate, EnvironmentUpdate

class EnvironmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, env_in: EnvironmentCreate) -> Environment:
        env = Environment(**env_in.model_dump())
        self.db.add(env)
        try:
            self.db.flush()
            return env
        except exc.IntegrityError:
            self.db.rollback()
            raise ValueError("Environment with this name already exists")

    def get_by_id(self, env_id: UUID) -> Optional[Environment]:
        return self.db.execute(
            select(Environment).where(Environment.id == env_id)
        ).scalar_one_or_none()

    def get_by_name(self, name: str) -> Optional[Environment]:
        return self.db.execute(
            select(Environment).where(Environment.name == name)
        ).scalar_one_or_none()

    def list(self, page: int = 1, page_size: int = 50) -> Tuple[List[Environment], int]:
        total = self.db.execute(select(func.count(Environment.id))).scalar_one()
        
        offset = (page - 1) * page_size
        items = self.db.execute(
            select(Environment)
            .order_by(Environment.created_at.desc())
            .offset(offset)
            .limit(page_size)
        ).scalars().all()
        
        return list(items), total

    def update(self, env: Environment, env_in: EnvironmentUpdate) -> Environment:
        update_data = env_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(env, field, value)
        try:
            self.db.flush()
            return env
        except exc.IntegrityError:
            self.db.rollback()
            raise ValueError("Environment with this name already exists")
