import json
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from app.core.config import settings

def get_fernet() -> Fernet:
    if not settings.INTEGRATION_ENCRYPTION_KEY:
        raise ValueError("INTEGRATION_ENCRYPTION_KEY is not configured")
    return Fernet(settings.INTEGRATION_ENCRYPTION_KEY.encode())

def encrypt_secret_payload(payload: Dict[str, Any]) -> Optional[str]:
    """
    Encrypts a dictionary of secrets into a base64 encoded string.
    """
    if not payload:
        return None
        
    fernet = get_fernet()
    json_str = json.dumps(payload)
    encrypted_bytes = fernet.encrypt(json_str.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")

def decrypt_secret_payload(encrypted_payload: Optional[str]) -> Dict[str, Any]:
    """
    Decrypts a base64 encoded string back into a dictionary.
    """
    if not encrypted_payload:
        return {}
        
    fernet = get_fernet()
    decrypted_bytes = fernet.decrypt(encrypted_payload.encode("utf-8"))
    return json.loads(decrypted_bytes.decode("utf-8"))

def extract_secrets(config: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Recursively scans configuration for keys matching secret signatures.
    Returns a tuple of (safe_config, extracted_secrets).
    """
    safe_config = {}
    extracted_secrets = {}
    
    SECRET_SUFFIXES = ("password", "token", "secret", "api_key", "access_token", "client_secret")
    
    def is_secret_key(key: str) -> bool:
        k = key.lower()
        for suffix in SECRET_SUFFIXES:
            if k == suffix or k.endswith(f"_{suffix}"):
                return True
        return False

    for k, v in config.items():
        if isinstance(v, dict):
            child_safe, child_secrets = extract_secrets(v)
            if child_safe:
                safe_config[k] = child_safe
            if child_secrets:
                extracted_secrets[k] = child_secrets
        elif is_secret_key(k):
            extracted_secrets[k] = v
        else:
            safe_config[k] = v
            
    return safe_config, extracted_secrets
