from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AWSEndpointOverrides(BaseModel):
    ec2: Optional[str] = None
    sts: Optional[str] = None
    s3: Optional[str] = None


class AWSIntegrationConfig(BaseModel):
    region: str = Field(..., description="AWS Region (e.g. us-east-1)")
    role_arn: Optional[str] = Field(None, description="Optional IAM Role ARN to assume")
    external_id: Optional[str] = Field(None, description="Optional External ID for role assumption")
    endpoint_overrides: Optional[AWSEndpointOverrides] = Field(
        None, description="Optional endpoint overrides for testing (e.g. LocalStack)"
    )
    verify_tls: bool = Field(True, description="Whether to verify TLS certificates")


class AWSIntegrationSecrets(BaseModel):
    access_key_id: Optional[str] = Field(None, description="AWS Access Key ID")
    secret_access_key: Optional[str] = Field(None, description="AWS Secret Access Key")
    session_token: Optional[str] = Field(None, description="Optional AWS Session Token")
