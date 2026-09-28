from pydantic import BaseModel, Field

class ScaleDeploymentParams(BaseModel):
    desired_replicas: int = Field(..., ge=0, le=50, description="The desired number of replicas (bounded 0-50)")

class VerificationState(BaseModel):
    attempt: int = 0
    max_attempts: int = 15
    initial_pod_name: str = ""
    replacement_pod_name: str = ""
