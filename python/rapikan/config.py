"""Rapikan application configuration (Pydantic Settings)."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RAPIKAN_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Storage ---
    base_documents_dir: Path = Field(
        default=Path("documents"),
        description="Root directory for uploaded documents (absolute).",
    )

    # --- Security limits ---
    max_file_size_mb: int = Field(default=50, ge=1, le=500)
    max_zip_entries: int = Field(default=1000, ge=1)
    max_zip_ratio: int = Field(
        default=100,
        ge=1,
        description="Max allowed uncompressed/compressed ratio (zip-bomb check).",
    )

    # --- Document retention ---
    document_ttl_days: int = Field(default=30, ge=1)

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


# Module-level singleton – override in tests via env vars or monkeypatching.
settings = Settings()
