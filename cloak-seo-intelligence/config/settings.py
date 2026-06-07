"""Typed, environment-driven configuration for cloak-seo-intelligence.

All configuration lives here so the rest of the codebase never reads
``os.environ`` directly. Values come from environment variables or a local
``.env`` file (see ``.env.example``).
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, populated from the environment / ``.env``."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Letta runtime ────────────────────────────────────────────────────────
    letta_base_url: str = Field(
        default="http://localhost:8283",
        alias="LETTA_BASE_URL",
        description="Base URL of the Letta server (self-hosted or cloud).",
    )
    letta_api_key: str | None = Field(
        default=None,
        alias="LETTA_API_KEY",
        description="API key for Letta Cloud; unset for a self-hosted server.",
    )

    # ── Models ────────────────────────────────────────────────────────────────
    llm_model: str = Field(default="openai/local-mlx", alias="CLOAK_LLM_MODEL")
    embedding_model: str = Field(
        default="openai/text-embedding-3-small", alias="CLOAK_EMBEDDING_MODEL"
    )
    context_window: int = Field(default=16000, alias="CLOAK_CONTEXT_WINDOW")

    # ── Storage ─────────────────────────────────────────────────────────────────
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # ── Market / deployment ──────────────────────────────────────────────────
    market_name: str = Field(default="Fort Lauderdale, FL", alias="CLOAK_MARKET_NAME")
    market_location_code: str = Field(
        default="1015214", alias="CLOAK_MARKET_LOCATION_CODE"
    )
    market_language: str = Field(default="en", alias="CLOAK_MARKET_LANGUAGE")

    # ── External providers (data pipeline / RL — next milestone) ─────────────
    dataforseo_login: str | None = Field(default=None, alias="DATAFORSEO_LOGIN")
    dataforseo_password: str | None = Field(default=None, alias="DATAFORSEO_PASSWORD")

    # ── Logging ──────────────────────────────────────────────────────────────
    log_level: str = Field(default="INFO", alias="CLOAK_LOG_LEVEL")

    @property
    def is_cloud(self) -> bool:
        """True when configured against Letta Cloud (an API key is set)."""
        return bool(self.letta_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached, validated :class:`Settings` instance."""
    return Settings()  # type: ignore[call-arg]
