import pytest
from app.core.encryption import extract_secrets, encrypt_secret_payload, decrypt_secret_payload
from cryptography.fernet import Fernet

def test_extract_secrets():
    config = {
        "url": "http://example.com",
        "username": "admin",
        "password": "supersecretpassword",
        "nested": {
            "api_token": "some_token",
            "safe_key": "safe_value"
        }
    }
    
    safe_config, extracted_secrets = extract_secrets(config)
    
    assert "password" not in safe_config
    assert "api_token" not in safe_config["nested"]
    assert "safe_key" in safe_config["nested"]
    assert "url" in safe_config
    
    assert extracted_secrets["password"] == "supersecretpassword"
    assert extracted_secrets["nested"]["api_token"] == "some_token"

def test_encrypt_decrypt_secret_payload(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("INTEGRATION_ENCRYPTION_KEY", key)
    # Refresh settings locally or just mock the get_fernet since settings might be loaded
    # A cleaner way is to mock get_fernet
    
    import app.core.encryption
    original_get_fernet = app.core.encryption.get_fernet
    app.core.encryption.get_fernet = lambda: Fernet(key.encode())
    
    try:
        secrets = {"token": "12345"}
        encrypted = encrypt_secret_payload(secrets)
        assert encrypted is not None
        assert encrypted != '{"token": "12345"}'
        
        decrypted = decrypt_secret_payload(encrypted)
        assert decrypted["token"] == "12345"
    finally:
        app.core.encryption.get_fernet = original_get_fernet
