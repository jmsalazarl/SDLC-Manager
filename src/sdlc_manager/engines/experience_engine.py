from __future__ import annotations

from uuid import UUID

from ..domain.models import EngineeringExperience
from ..domain.ports.repositories import ExperienceRepository


class ExperienceEngine:
    def __init__(self, repository: ExperienceRepository) -> None:
        self.repository = repository

    def search(
        self,
        query: str | None = None,
        component: str | None = None,
        tags: list[str] | None = None,
        include_unreviewed: bool = False,
        project_id: UUID | None = None,
    ) -> list[EngineeringExperience]:
        return self.repository.search(query, component, tags, include_unreviewed, project_id)
