from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str

    JWT_SECRET: str
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 30
    REFRESH_TOKEN_DAYS: int = 14

    CORS_ORIGINS: str = ""
    LOG_LEVEL: str = "INFO"

    MEDIA_DIR: str = "/app/media"
    MEDIA_URL_PREFIX: str = "/media"

    BOT_ADMIN_SECRET: str = ""
    BOT_USER_SECRET: str = ""
    TELEGRAM_LINK_TTL_SECONDS: int = 600

    REDIS_URL: str = "redis://redis:6379/0"
    PRODUCTS_CACHE_TTL_SECONDS: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("CORS_ORIGINS")
    @classmethod
    def normalize_origins(cls, value: str) -> str:
        return value.strip()

    def cors_list(self) -> List[str]:
        if not self.CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
