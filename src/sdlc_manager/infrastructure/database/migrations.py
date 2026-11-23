from __future__ import annotations

from alembic import command
from alembic.config import Config

from ...config import Settings


def run_migrations(settings: Settings) -> None:
    migration_root = settings.project_root
    if not (migration_root / "migrations").is_dir():
        migration_root = settings.resource_root
    config = Config(str(migration_root / "alembic.ini"))
    config.set_main_option("script_location", str(migration_root / "migrations"))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(config, "head")
