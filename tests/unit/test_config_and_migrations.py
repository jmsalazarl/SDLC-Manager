from __future__ import annotations

from pathlib import Path

from sdlc_manager.config import Settings
from sdlc_manager.infrastructure.database.migrations import run_migrations


def test_resolve_path_prefers_absolute_then_project_then_resources(tmp_path: Path) -> None:
    settings = Settings(project_root=tmp_path)
    absolute = tmp_path / "absolute.yaml"
    (tmp_path / "local.yaml").write_text("x", encoding="utf-8")

    assert settings.resolve_path(absolute) == absolute
    assert settings.resolve_path("local.yaml") == tmp_path / "local.yaml"
    assert settings.resolve_path("knowledge/rules") == settings.resource_root / "knowledge/rules"
    assert settings.resolved_policy_paths() == [settings.resource_root / "knowledge/rules"]


def test_run_migrations_falls_back_to_resource_root(tmp_path: Path) -> None:
    database = tmp_path / "db.sqlite"
    settings = Settings(project_root=tmp_path, database_url=f"sqlite:///{database}")

    run_migrations(settings)

    assert database.is_file()
