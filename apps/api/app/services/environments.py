from typing import List, Tuple, Any, Dict
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.environment import Environment
from app.models.user import User
from app.schemas.inventory import EnvironmentCreate, EnvironmentUpdate
from app.repositories.environments import EnvironmentRepository
from app.services.audit import log_event

class EnvironmentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = EnvironmentRepository(db)

    def create(self, env_in: EnvironmentCreate, current_user: User, request_id: str = None) -> Environment:
        existing = self.repo.get_by_name(env_in.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Environment with this name already exists"
            )
            
        env = self.repo.create(env_in)
        
        log_event(
            db=self.db,
            actor_user_id=current_user.id,
            action="environment.created",
            resource_type="environment",
            resource_id=str(env.id),
            result="success",
            request_id=request_id,
            metadata={"name": env.name}
        )
        
        return env

    def get_by_id(self, env_id: UUID) -> Environment:
        env = self.repo.get_by_id(env_id)
        if not env:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Environment not found"
            )
        return env

    def list(self, page: int = 1, page_size: int = 50) -> Tuple[List[Environment], int]:
        return self.repo.list(page=page, page_size=page_size)

    def update(self, env_id: UUID, env_in: EnvironmentUpdate, current_user: User, request_id: str = None) -> Environment:
        env = self.get_by_id(env_id)
        
        if env_in.name and env_in.name != env.name:
            existing = self.repo.get_by_name(env_in.name)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Environment with this name already exists"
                )
                
        updated_env = self.repo.update(env, env_in)
        
        log_event(
            db=self.db,
            actor_user_id=current_user.id,
            action="environment.updated",
            resource_type="environment",
            resource_id=str(updated_env.id),
            result="success",
            request_id=request_id,
            metadata={"name": updated_env.name}
        )
        
        return updated_env
