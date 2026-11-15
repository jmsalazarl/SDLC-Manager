from __future__ import annotations

from pathlib import PurePath
from typing import Any

from ..domain.models import EngineeringPractice


class PracticeEngine:
    """Evalua recomendaciones contextuales sin producir bloqueos."""

    def __init__(self, practices: list[EngineeringPractice]) -> None:
        self.practices = practices

    def applicable(self, context: dict[str, Any]) -> list[EngineeringPractice]:
        return [
            practice
            for practice in self.practices
            if practice.enabled and self._matches_practice(practice, context)
        ]

    @classmethod
    def _matches_practice(cls, practice: EngineeringPractice, context: dict[str, Any]) -> bool:
        triggers = practice.triggers
        project_id = context.get("project_id")
        owner_id = context.get("actor_id")
        organization_id = context.get("organization_id")
        if practice.scope.value == "PROJECT" and str(practice.project_id) != str(project_id):
            return False
        if practice.scope.value == "PERSONAL" and practice.owner_id != owner_id:
            return False
        if practice.scope.value == "ORGANIZATION" and practice.organization_id != organization_id:
            return False
        event = triggers.get("event")
        if event and event != context.get("event"):
            return False
        stage = triggers.get("stage")
        if stage and stage != context.get("stage"):
            return False
        components = triggers.get("components")
        if components and context.get("component") not in components:
            return False
        extensions = triggers.get("file_extensions")
        if extensions:
            files = context.get("changed_files", [])
            if not any(PurePath(str(item)).suffix.lower() in extensions for item in files):
                return False
        return True
