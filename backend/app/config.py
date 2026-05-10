"""App configuration loaded from .env / environment variables.

DATA_DIR controls where mutable state lives (seed CSV, local JSON store,
discovered seeds). Default is `backend/data` so local development keeps
working with no env var set; in hosted environments point it at a mounted
volume, e.g. DATA_DIR=/data on Railway or Render.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Fallback default: <repo>/backend/data — the same path that worked before
# DATA_DIR was a setting.
_DEFAULT_DATA_DIR = (Path(__file__).resolve().parent.parent / "data").as_posix()


class Settings(BaseSettings):
    # External calls
    enable_external_api_calls: bool = False
    anthropic_api_key: str = ""
    exa_api_key: str = ""

    # Storage / hosting
    data_dir: str = _DEFAULT_DATA_DIR
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Crawler
    user_agent: str = "IntegrationScoutBot/0.2 contact=you@example.com"
    request_timeout_seconds: float = 15.0

    # Legacy alias kept so old .env files don't break — superseded by data_dir.
    database_path: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def data_path(self) -> Path:
        """Resolved path to the data directory. Created on first use."""
        path = Path(self.data_dir).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def companies_store_path(self) -> Path:
        return self.data_path / "companies.json"

    @property
    def seed_csv_path(self) -> Path:
        return self.data_path / "seed_companies.csv"

    @property
    def discovery_csv_path(self) -> Path:
        return self.data_path / "discovered_seeds.csv"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    """Force re-read of env vars on next get_settings() call. Test-only helper."""
    get_settings.cache_clear()


# Convenience for callers that want to opt out of the cache (e.g. tests that
# mutate os.environ between cases).
def settings_from_env() -> Settings:
    return Settings()


# Make DATA_DIR observable on import for one-time setup (e.g. ensuring the dir
# exists before the JSON store tries to open it).
os.makedirs(get_settings().data_dir, exist_ok=True)
