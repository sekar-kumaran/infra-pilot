from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.database.session import get_db
from app.services.policy_engine import PolicyEngine
from app.models.enums import PolicyDecisionType
from app.api.deps import get_current_user
from app.models.user import User
from app.models.policy import Policy

router = APIRouter()

class PolicySimulationRequest(BaseModel):
    provider: Optional[str] = None
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    action: Optional[str] = None
    risk: Optional[str] = None
    severity: Optional[str] = None
    environment: Optional[str] = None

class PolicySimulationResponse(BaseModel):
    decision: str
    risk: Optional[str] = None
    matched_policies: List[str] = []
    reason: str

@router.get("/")
def list_policies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    policies = db.query(Policy).all()
    result = []
    for p in policies:
        result.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "policy_type": p.policy_type,
            "status": p.status,
            "action_type": p.action_type
        })
    return result

@router.post("/simulate", response_model=PolicySimulationResponse)
def simulate_policy(
    request: PolicySimulationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Simulate a policy decision based on contextual attributes without mutating state.
    """
    engine = PolicyEngine(db)
    
    context = {
        "provider": request.provider,
        "resource_id": request.resource_id,
        "resource_type": request.resource_type,
        "action_type": [request.action] if request.action else [],
        "risk_level": request.risk,
        "incident_severity": request.severity,
        "environment": request.environment
    }
    
    decision, reason, matched_policy = engine.simulate(context)
    
    return PolicySimulationResponse(
        decision=decision.value,
        risk=request.risk,
        matched_policies=[matched_policy.name] if matched_policy else [],
        reason=reason
    )
