"""Environment-backed configuration without exposing secret values."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    from .models import SearchAPI
except ImportError:  # Support direct imports with ``backend/src`` on sys.path.
    from models import SearchAPI  # type: ignore[no-redef]


class Settings(BaseSettings):
    """Runtime settings shared by the API and later service implementations."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: str = ""
    llm_model_id: str = ""
    llm_api_key: str = ""
    llm_base_url: str = ""

    search_api: SearchAPI = SearchAPI.DUCKDUCKGO
    tavily_api_key: str = ""
    perplexity_api_key: str = ""
    searxng_url: str = ""

    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    cors_origins: str = "http://localhost:5174"
    notes_workspace: str = "./workspace"
    search_cache_dir: str = "./cache/search"

    @property
    def cors_origin_list(self) -> list[str]:
        """Return normalized CORS origins from a comma-separated env value."""
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    def integration_status(self) -> dict[str, bool]:
        """Report configuration presence only; no external request is made."""
        search_api = self.search_api.value
        search_ready = {
            "duckduckgo": True,
            "tavily": bool(self.tavily_api_key),
            "perplexity": bool(self.perplexity_api_key),
            "searxng": bool(self.searxng_url),
            "advanced": True,
        }.get(search_api, False)
        return {
            "llm": bool(self.llm_model_id and self.llm_api_key),
            "search": search_ready,
            "notes": bool(self.notes_workspace.strip()),
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Create one settings object per process."""
    return Settings()
