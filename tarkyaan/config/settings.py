"""
Configuration management for Tarkyaan.
Independent from NOVA settings.
"""

from __future__ import annotations

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TarkyaanSettings(BaseSettings):
    """
    Tarkyaan application and memory settings.
    """
    model_config = SettingsConfigDict(
        env_prefix="TARKYAAN_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Tarkyaan"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    # Persistent storage
    database_path: str = Field(
        default="data/tarkyaan.db",
        description="Path to Tarkyaan SQLite database file"
    )

    # Mastery Engine Parameters
    default_mastery_learning_rate: float = Field(
        default=0.25,
        ge=0.01,
        le=1.0,
        description="Alpha parameter in evidence update"
    )
    uncertainty_decay_rate: float = Field(
        default=0.75,
        ge=0.1,
        le=0.99,
        description="Uncertainty multiplier on evidence update"
    )

    # Retention Engine Parameters
    default_retention_half_life_days: float = Field(
        default=14.0,
        ge=1.0,
        le=365.0,
        description="Default concept stability factor (days)"
    )
    default_retention_baseline: float = Field(
        default=0.1,
        ge=0.0,
        le=0.5,
        description="Floor baseline mastery below which decay will not drop"
    )

    # Contextual Retrieval
    default_retrieval_token_budget: int = Field(
        default=1500,
        ge=100,
        le=8000,
        description="Token budget for contextual memory retrieval"
    )

    def get_resolved_db_path(self, base_dir: Path | None = None) -> Path:
        """Resolve database path against base directory."""
        p = Path(self.database_path)
        if p.is_absolute():
            return p
        base = base_dir or Path.cwd()
        return (base / p).resolve()


# Singleton instance
settings = TarkyaanSettings()
