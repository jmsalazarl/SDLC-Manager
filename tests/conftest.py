from __future__ import annotations

from pathlib import Path

import pytest

from sdlc_manager.config import Settings
from sdlc_manager.infrastructure.container import ApplicationContainer, build_container


@pytest.fixture
def container(tmp_path: Path) -> ApplicationContainer:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        policy_paths=[str(Path(__file__).parents[1] / "knowledge" / "rules")],
        project_root=Path(__file__).parents[1],
    )
    return build_container(settings)
