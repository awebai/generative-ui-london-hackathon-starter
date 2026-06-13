from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the genui server."""

    model_config = SettingsConfigDict(env_prefix="GENUI_SERVER_", env_file=".env", extra="ignore")

    database_url: str = Field(default="postgresql://localhost/genui")
    awid_registry_url: str = Field(default="https://api.awid.ai")
    public_origin: str = Field(default="http://127.0.0.1:8200")
    auth_cache_ttl_seconds: int = Field(default=600, ge=1)
    timestamp_skew_seconds: int = Field(default=300, ge=1)
    default_present_ttl_seconds: int = Field(default=86_400, ge=60)
    max_present_ttl_seconds: int = Field(default=604_800, ge=60)


def get_settings() -> Settings:
    return Settings()
