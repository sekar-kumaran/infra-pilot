from typing import Optional, Any
from pydantic import BaseModel, HttpUrl, Field

class NagiosIntegrationConfig(BaseModel):
    base_url: str = Field(..., description="Base URL of the Nagios instance")
    status_endpoint: str = Field(
        default="/nagios/cgi-bin/status.dat",
        description="Endpoint path for status.dat or equivalent status JSON"
    )
    timeout_seconds: int = Field(default=10, description="HTTP connection timeout in seconds")
    tls_verify: bool = Field(default=True, description="Verify TLS certificates")

class NagiosHostStatus(BaseModel):
    host_name: str
    current_state: int
    plugin_output: str = ""
    last_check: int = 0
    last_state_change: int = 0
    current_attempt: int = 1
    max_attempts: int = 1
    problem_has_been_acknowledged: int = 0
    notifications_enabled: int = 1

class NagiosServiceStatus(BaseModel):
    host_name: str
    service_description: str
    current_state: int
    plugin_output: str = ""
    last_check: int = 0
    last_state_change: int = 0
    current_attempt: int = 1
    max_attempts: int = 1
    problem_has_been_acknowledged: int = 0
    notifications_enabled: int = 1
