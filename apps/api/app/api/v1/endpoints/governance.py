from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api.deps import get_db, get_current_user

router = APIRouter()

@router.get("/compliance")
def get_compliance_report(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from app.models.policy import Policy
    
    policies = db.query(Policy).all()
    
    # We will simulate compliance scanning against actual active policies in DB
    total_policies = len(policies)
    if total_policies == 0:
        return {
            "global_score": 0,
            "global_passing": 0,
            "global_failing": 0,
            "frameworks": [],
            "findings": []
        }
    
    # Since we don't have real "evaluations" persisted yet, 
    # we represent the active policies as passing and inactive as failing,
    # or just show there are no actual failing findings if resources are minimal.
    # To use REAL data, let's just count active policies as passing controls for now
    # to prove it's connected to DB.
    
    passing = sum(1 for p in policies if p.status == 'ACTIVE')
    failing = total_policies - passing
    
    return {
        "global_score": round((passing / total_policies) * 100) if total_policies > 0 else 100,
        "global_passing": passing,
        "global_failing": failing,
        "frameworks": [
            {
                "id": "ip-sec-1",
                "name": "InfraPilot Security Baseline",
                "provider": "global",
                "score": round((passing / total_policies) * 100) if total_policies > 0 else 100,
                "passing": passing,
                "failing": failing
            }
        ],
        "findings": []
    }
