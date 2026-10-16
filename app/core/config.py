from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    telegram_bot_token: str = ""
    admin_telegram_ids: str = ""
    database_url: str = "postgresql+asyncpg://cs2:cs2@postgres:5432/cs2analytics"
    redis_url: str = "redis://redis:6379/0"
    pandascore_token: str = ""
    pandascore_base_url: str = "https://api.pandascore.co"
    min_maps_for_ranking: int = 20
    log_level: str = "INFO"

    @property
    def admins(self) -> set[int]:
        return {int(value) for value in self.admin_telegram_ids.split(",") if value.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
