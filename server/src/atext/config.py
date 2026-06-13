from __future__ import annotations

from typing import Self

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the genui server."""

    model_config = SettingsConfigDict(env_prefix="GENUI_SERVER_", env_file=".env", extra="ignore")

    database_url: str = Field(default="postgresql://localhost/genui")
    awid_registry_url: str = Field(default="https://api.awid.ai")
    public_origin: str = Field(default="http://127.0.0.1:8200")
    presentation_origin: str | None = Field(default=None)
    auth_cache_ttl_seconds: int = Field(default=600, ge=1)
    timestamp_skew_seconds: int = Field(default=300, ge=1)
    default_present_ttl_seconds: int = Field(default=86_400, ge=60)
    max_present_ttl_seconds: int = Field(default=604_800, ge=60)
    db_pool_min_connections: int = Field(default=1, ge=1)
    db_pool_max_connections: int = Field(default=5, ge=1)
    db_statement_cache_size: int = Field(default=0, ge=0)
    linkup_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LINKUP_API_KEY", "GENUI_SERVER_LINKUP_API_KEY", "linkup_api_key"),
    )

    @model_validator(mode="after")
    def validate_db_pool(self) -> Self:
        if self.db_pool_max_connections < self.db_pool_min_connections:
            raise ValueError("db_pool_max_connections must be >= db_pool_min_connections")
        return self


def get_settings() -> Settings:
    return Settings()
