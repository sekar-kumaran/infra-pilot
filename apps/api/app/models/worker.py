import uuid
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database.base import Base

class WorkerNode(Base):
    __tablename__ = "worker_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    worker_id = Column(String(255), nullable=False, unique=True, index=True)
    hostname = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="ONLINE", index=True)
    
    active_tasks = Column(Integer, nullable=False, default=0)
    queue = Column(String(255), nullable=True)
    concurrency = Column(Integer, nullable=False, default=1)
    version = Column(String(50), nullable=True)

    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
