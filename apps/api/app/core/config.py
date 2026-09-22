from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator

class Settings(BaseSettings):
    APP_NAME: str = "InfraPilot API"
    APP_ENV: str = "development"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    
    DATABASE_URL: str = ""
    REDIS_URL: str = ""
    RABBITMQ_URL: str = ""
    
    CORS_ALLOWED_ORIGINS: Union[str, List[str]] = []
    
    # Auth configuration
    AUTH_SECRET_KEY: str = ""
    AUTH_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Integrations configuration
    INTEGRATION_ENCRYPTION_KEY: str = ""
    INTEGRATION_DEFAULT_TIMEOUT_SECONDS: int = 30
    INTEGRATION_MAX_RETRIES: int = 3
    INTEGRATION_BACKOFF_SECONDS: int = 5
    
    # Celery configuration
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""
    
    @field_validator("CORS_ALLOWED_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
