# Pydantic Settings：读取 .env，暴露全局 settings 对象
import os
import sys
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_database_url() -> str:
    # 打包成 .exe 后当前工作目录可能不可写（如 Program Files），数据库放到用户数据目录
    if not getattr(sys, "frozen", False):
        return "sqlite:///./test_platform.db"
    data_dir = Path(os.getenv("APPDATA") or Path.home()) / "VasoRAT"
    data_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{(data_dir / 'vasorat.db').as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Test Platform"
    API_PREFIX: str = "/api/v1"
    DATABASE_URL: str = Field(default_factory=_default_database_url)
    CORS_ORIGINS: list[str] = ["*"]
    LOG_LEVEL: str = "INFO"


settings = Settings()