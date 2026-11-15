from __future__ import annotations

from typing import Protocol
from uuid import UUID

from ..enums import ReviewStatus
from ..models import (
    AuditEntry,
    EngineeringExperience,
    EngineeringPractice,
    Evidence,
    PolicyEvaluation,
    ProcessedEvent,
    Project,
    SdlcException,
    SdlcGate,
    SdlcStage,
    SdlcWorkflow,
    Sprint,
    UserStory,
)


class ProjectRepository(Protocol):
    def save(self, project: Project) -> Project: ...

    def get(self, project_id: UUID) -> Project | None: ...

    def list_all(self) -> list[Project]: ...


class SprintRepository(Protocol):
    def save(self, sprint: Sprint) -> Sprint: ...

    def list_by_project(self, project_id: UUID) -> list[Sprint]: ...


class UserStoryRepository(Protocol):
    def save(self, story: UserStory) -> UserStory: ...

    def get_for_project(self, project_id: UUID, story_id: UUID) -> UserStory | None: ...

    def list_by_project(
        self, project_id: UUID, sprint_id: UUID | None = None
    ) -> list[UserStory]: ...


class ExperienceRepository(Protocol):
    def save(self, experience: EngineeringExperience) -> EngineeringExperience: ...

    def search(
        self,
        query: str | None = None,
        component: str | None = None,
        tags: list[str] | None = None,
        include_unreviewed: bool = False,
        project_id: UUID | None = None,
    ) -> list[EngineeringExperience]: ...

    def get(self, experience_id: UUID) -> EngineeringExperience | None: ...

    def save_review(
        self,
        experience_id: UUID,
        status: ReviewStatus,
        reviewed_by: str,
    ) -> EngineeringExperience: ...


class WorkflowRepository(Protocol):
    def save_workflow(self, workflow: SdlcWorkflow) -> SdlcWorkflow: ...

    def save_stage(self, stage: SdlcStage) -> SdlcStage: ...

    def save_gate(self, gate: SdlcGate) -> SdlcGate: ...

    def save_exception(self, exception: SdlcException) -> SdlcException: ...

    def get(self, workflow_id: UUID) -> SdlcWorkflow | None: ...

    def get_by_code_version(self, code: str, version: str) -> SdlcWorkflow | None: ...

    def list_stages(self, workflow_id: UUID) -> list[SdlcStage]: ...

    def list_gates(self, workflow_id: UUID) -> list[SdlcGate]: ...

    def list_exceptions(self, workflow_id: UUID) -> list[SdlcException]: ...


class PracticeRepository(Protocol):
    def save(self, practice: EngineeringPractice) -> EngineeringPractice: ...

    def list(self, include_unapproved: bool = False) -> list[EngineeringPractice]: ...

    def get(self, practice_id: UUID) -> EngineeringPractice | None: ...

    def save_review(
        self, practice_id: UUID, status: ReviewStatus, reviewed_by: str
    ) -> EngineeringPractice: ...


class EvidenceRepository(Protocol):
    def save(self, evidence: Evidence) -> Evidence: ...

    def get_for_project(self, project_id: UUID, evidence_id: UUID) -> Evidence | None: ...

    def list_for_story_and_policy(
        self, project_id: UUID, story_id: UUID | None, policy_id: str
    ) -> list[Evidence]: ...

    def list_for_story(self, project_id: UUID, story_id: UUID) -> list[Evidence]: ...


class EvaluationRepository(Protocol):
    def save(self, evaluation: PolicyEvaluation) -> PolicyEvaluation: ...


class AuditRepository(Protocol):
    def save(self, entry: AuditEntry) -> AuditEntry: ...


class ExceptionApprovalAuthority(Protocol):
    def is_authorized(self, exception: SdlcException) -> bool: ...


class EventRepository(Protocol):
    def get(self, event_id: UUID) -> ProcessedEvent | None: ...

    def save(self, event: ProcessedEvent) -> ProcessedEvent: ...
