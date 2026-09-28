import re
from typing import Any

def sanitize_identifier(value: Any) -> str:
    """
    Validates and sanitizes standard identifiers (service names, container names).
    Must not contain shell control characters.
    """
    if not isinstance(value, str):
        value = str(value)
        
    value = value.strip()
    
    if len(value) == 0 or len(value) > 255:
        raise ValueError("Identifier length must be between 1 and 255 characters")
        
    # Only allow alphanumerics, dashes, underscores, and dots
    if not re.match(r'^[\w\-\.]+$', value):
        raise ValueError(f"Invalid characters in identifier: {value}")
        
    return value

def redact_sensitive_data(output: str) -> str:
    """
    Scrub potentially sensitive information from Ansible output.
    """
    if not output:
        return output
        
    # Extremely basic redaction (in a real system this would use the global secret manager)
    output = re.sub(r'bearer\s+[\w\-._~+]+', 'bearer [REDACTED]', output, flags=re.IGNORECASE)
    output = re.sub(r'password[\s:=]+[\S]+', 'password: [REDACTED]', output, flags=re.IGNORECASE)
    output = re.sub(r'token[\s:=]+[\S]+', 'token: [REDACTED]', output, flags=re.IGNORECASE)
    output = re.sub(r'private_key[\s:=]+[\S]+', 'private_key: [REDACTED]', output, flags=re.IGNORECASE)
    
    return output
