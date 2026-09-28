import uuid
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base
from app.models.enums import PolicyDecisionType, RiskLevel

class Policy(Base):
    __tablename__ = "policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=100)  # Lower number = higher priority
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    rules = relationship("PolicyRule", back_populates="policy", cascade="all, delete-orphan")


class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False)
    field = Column(String(255), nullable=False)  # e.g., 'action_type', 'resource_type', 'risk_level'
    operator = Column(String(50), nullable=False) # e.g., 'EQUALS', 'IN', 'GREATER_THAN'
    expected_value = Column(JSON, nullable=False)
    risk_level = Column(String(50), nullable=True) # Optional override for calculated risk
    decision = Column(String(50), nullable=False, default=PolicyDecisionType.DENY.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    policy = relationship("Policy", back_populates="rules")


class PolicyDecision(Base):
    __tablename__ = "policy_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("automation_executions.id", ondelete="CASCADE"), nullable=False, unique=True)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id", ondelete="SET NULL"), nullable=True)
    decision = Column(String(50), nullable=False)
    risk_level = Column(String(50), nullable=False)
    reason = Column(Text, nullable=True)
    evaluated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    execution = relationship("AutomationExecution")
    policy = relationship("Policy")
