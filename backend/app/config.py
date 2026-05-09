from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    enable_external_api_calls: bool = False
    anthropic_api_key: str = ""
    exa_api_key: str = ""
    database_path: str = "backend/data/radar.sqlite3"
    user_agent: str = "IntegrationRadarBot/0.2"
    request_timeout_seconds: float = 15.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
