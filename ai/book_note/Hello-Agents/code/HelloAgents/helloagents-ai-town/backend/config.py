"""Runtime configuration for the Cyber Town backend."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parent / ".env"


class Settings(BaseSettings):
    """Load local settings without making network connections at import time."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_host: str = "0.0.0.0"
    api_port: int = Field(default=8000, ge=1, le=65535)
    cors_origins: str = "http://localhost:8060,http://127.0.0.1:8060"

    llm_model_id: str = ""
    llm_api_key: str = ""
    llm_base_url: str = ""
    memory_path: str = "./memory_data"
    qdrant_url: str = "http://127.0.0.1:6333"
    sqlite_path: str = "./data/cyber_town.db"
    log_path: str = "./logs"
    npc_update_interval: int = Field(default=30, ge=1)

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    def integration_status(self) -> dict[str, bool]:
        """Report configuration presence only; no external service is contacted."""
        return {
            "llm": self.llm_configured,
            "qdrant": bool(self.qdrant_url.strip()),
            "sqlite": bool(self.sqlite_path.strip()),
        }

    @property
    def llm_configured(self) -> bool:
        return all(
            value.strip()
            for value in (
                self.llm_model_id,
                self.llm_api_key,
                self.llm_base_url,
            )
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
