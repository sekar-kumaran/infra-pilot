from app.core.config import Settings

def test_config_defaults():
    settings = Settings(_env_file=None)
    assert settings.APP_NAME == "InfraPilot API"
    assert settings.APP_ENV == "development"
