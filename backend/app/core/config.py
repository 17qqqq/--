# Pydantic Settings：读取 .env，暴露全局 settings 对象
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Test Platform"
    API_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./test_platform.db"
    CORS_ORIGINS: list[str] = ["*"]
    LOG_LEVEL: str = "INFO"


settings = Settings()