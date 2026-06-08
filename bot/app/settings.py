from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str

    API_URL: str | None = None
    BOT_ADMINS: str = ""

    API_BASE_URL: str | None = None
    ADMIN_IDS: str = ""

    BOT_ADMIN_SECRET: str = ""
    BOT_USER_SECRET: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def api_base_url(self) -> str:
        return (self.API_URL or self.API_BASE_URL or "http://backend:8000").rstrip("/")

    def admins(self) -> set[int]:
        raw = self.BOT_ADMINS or self.ADMIN_IDS
        if not raw.strip():
            return set()
        return {int(x.strip()) for x in raw.split(",") if x.strip()}


settings = Settings()
