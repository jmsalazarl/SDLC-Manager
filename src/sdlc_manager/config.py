from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuracion de ejecucion sin dependencias de servicios externos."""

    model_config = SettingsConfigDict(
        env_prefix="SDLC_MANAGER_",
        env_file=".env",
        extra="ignore",
    )

    database_url: str = "sqlite:///./data/sdlc_manager.db"
    policy_paths: list[str] = Field(default_factory=lambda: ["knowledge/rules"])
    workflow_template_path: str = "knowledge/sdlc/default.yaml"
    log_level: str = "WARNING"
    auto_migrate: bool = True
    project_root: Path = Field(default_factory=lambda: Path.cwd())

    @property
    def resource_root(self) -> Path:
        """Devuelve la raiz instalada que contiene migraciones y conocimiento."""
        return Path(__file__).resolve().parents[2]

    def resolved_policy_paths(self) -> list[Path]:
        return [self.resolve_path(item) for item in self.policy_paths]

    def resolve_path(self, value: str | Path) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        project_path = self.project_root / path
        if project_path.exists():
            return project_path
        return self.resource_root / path


@lru_cache
def get_settings() -> Settings:
    return Settings()
