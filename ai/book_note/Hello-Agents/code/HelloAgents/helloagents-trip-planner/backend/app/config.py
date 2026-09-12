"""Environment-backed settings for the travel assistant backend."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Load non-secret defaults and API credentials from ``.env``."""

    app_name: str = "HelloAgents 智能旅行助手"
    app_version: str = "0.1.0"
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:5173"

    llm_api_key: str = ""
    llm_model_id: str = ""
    llm_base_url: str = ""
    amap_maps_api_key: str = ""
    unsplash_access_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def allowed_origins(self) -> list[str]:
        """Return normalized origins for FastAPI's CORS middleware."""
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    def integration_status(self) -> dict[str, bool]:
        """Expose configuration presence without leaking credential values."""
        return {
            "llm": bool(self.llm_api_key and self.llm_model_id),
            "amap": bool(self.amap_maps_api_key),
            "unsplash": bool(self.unsplash_access_key),
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Create one immutable-by-convention settings object per process."""
    return Settings()

