"""App configuration, entirely environment-driven -- no key ever has a real
default value here (see .env.example)."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    log_level: str = "info"
    api_v1_prefix: str = "/api/v1"
    cors_allow_origins: str = "http://localhost:3000"

    database_url: str = "postgresql+psycopg://football_ai:football_ai@localhost:5432/football_ai"

    football_data_org_api_key: str = ""
    sportmonks_api_key: str = ""
    api_football_api_key: str = ""
    the_odds_api_key: str = ""
    betfair_app_key: str = ""
    betfair_username: str = ""
    betfair_password: str = ""

    anthropic_api_key: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


settings = Settings()
