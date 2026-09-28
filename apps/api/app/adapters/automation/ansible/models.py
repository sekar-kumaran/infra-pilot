from pydantic import BaseModel
from typing import Dict, Any, Optional

class AnsibleExecutionResult(BaseModel):
    success: bool
    return_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    error_message: Optional[str] = None
