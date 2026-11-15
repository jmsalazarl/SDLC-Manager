from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


def parse_uuid(value: Any) -> UUID:
    """Convert a JSON UUID string while preserving strict validation elsewhere."""
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        try:
            return UUID(value)
        except ValueError as error:
            raise ValueError("UUID must be a valid string") from error
    raise ValueError("UUID must be a UUID instance or string")


type UuidInput = Annotated[UUID, BeforeValidator(parse_uuid)]


class CreateProjectInput(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class CreateSprintInput(BaseModel):
    model_config = ConfigDict(strict=True)

    project_id: UuidInput
    name: str = Field(min_length=1, max_length=200)
    start_date: str | None = None
    end_date: str | None = None
    status: str = "PLANNED"


class CreateStoryInput(BaseModel):
    model_config = ConfigDict(strict=True)

    project_id: UuidInput
    sprint_id: UuidInput | None = None
    external_reference: str | None = Field(default=None, max_length=120)
    title: str = Field(min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=10000)
    acceptance_criteria: list[str] = Field(default_factory=list)
    dependencies: list[dict[str, Any]] = Field(default_factory=list)
    status: str = "DRAFT"


class ListPoliciesInput(BaseModel):
    model_config = ConfigDict(strict=True)

    status: str | None = None
    severity: str | None = None


class ApplicableRulesInput(BaseModel):
    model_config = ConfigDict(strict=True)

    project_id: UuidInput
    user_story_id: UuidInput | None = None
    event: str
    stage: str
    changed_files: list[str] = Field(default_factory=list)
    component: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class EvaluateGateInput(BaseModel):
    model_config = ConfigDict(strict=True)

    project_id: UuidInput
    user_story_id: UuidInput
    gate: str = Field(min_length=1, max_length=80)
    context: dict[str, Any] = Field(default_factory=dict)


class RegisterExperienceInput(BaseModel):
    model_config = ConfigDict(strict=True)

    title: str = Field(min_length=1, max_length=300)
    context: str = Field(min_length=1, max_length=10000)
    problem: str = Field(min_length=1, max_length=10000)
    root_cause: str = Field(min_length=1, max_length=10000)
    solution: str = Field(min_length=1, max_length=10000)
    lesson_learned: str = Field(min_length=1, max_length=10000)
    component: str | None = Field(default=None, max_length=160)
    tags: list[str] = Field(default_factory=list)
    related_policy_ids: list[str] = Field(default_factory=list)
    memory_type: str = "LESSON_LEARNED"
    technology: str | None = Field(default=None, max_length=120)
    category: str | None = Field(default=None, max_length=120)
    scope: str = "PERSONAL"
    project_id: UuidInput | None = None
    author: str | None = Field(default=None, max_length=160)
    related_experience_ids: list[UuidInput] = Field(default_factory=list)


class SearchExperiencesInput(BaseModel):
    model_config = ConfigDict(strict=True)

    query: str | None = None
    component: str | None = None
    tags: list[str] = Field(default_factory=list)
    include_unreviewed: bool = False


class RegisterEvidenceInput(BaseModel):
    model_config = ConfigDict(strict=True)

    project_id: UuidInput
    user_story_id: UuidInput
    policy_id: str = Field(min_length=1, max_length=120)
    evidence_type: str = Field(min_length=1, max_length=120)
    reference: str = Field(min_length=1, max_length=500)


class VerifyEvidenceInput(BaseModel):
    model_config = ConfigDict(strict=True)

    project_id: UuidInput
    evidence_id: UuidInput
    verified_by: str = Field(min_length=1, max_length=160)
    approved: bool = True


class AnalyzeStoryInput(BaseModel):
    model_config = ConfigDict(strict=True)

    project_id: UuidInput
    user_story_id: UuidInput


class StartSprintInput(BaseModel):
    model_config = ConfigDict(strict=True)

    project_id: UuidInput
    sprint_id: UuidInput | None = None


class ReviewExperienceInput(BaseModel):
    model_config = ConfigDict(strict=True)

    experience_id: UuidInput
    status: str = Field(pattern="^(PENDING|APPROVED|REJECTED)$")
    reviewed_by: str = Field(min_length=1, max_length=160)


class GetWorkflowInput(BaseModel):
    model_config = ConfigDict(strict=True)

    project_id: UuidInput


class CustomizeWorkflowInput(BaseModel):
    model_config = ConfigDict(strict=True)

    project_id: UuidInput
    name: str = Field(min_length=1, max_length=200)
    version: str = Field(min_length=1, max_length=40)
    stages: list[dict[str, Any]] = Field(min_length=1)
    exceptions: list[dict[str, Any]] = Field(default_factory=list)


class RegisterPracticeInput(BaseModel):
    model_config = ConfigDict(strict=True)

    title: str = Field(min_length=1, max_length=200)
    context: str = Field(min_length=1, max_length=10000)
    triggers: dict[str, Any] = Field(default_factory=dict)
    intervention_message: str = Field(min_length=1, max_length=10000)
    severity: str = Field(pattern="^(LOW|MEDIUM|HIGH)$")
    scope: str = Field(pattern="^(PERSONAL|PROJECT|ORGANIZATION)$")
    project_id: UuidInput | None = None
    owner_id: str | None = Field(default=None, max_length=160)
    organization_id: str | None = Field(default=None, max_length=160)
    source_experience_id: UuidInput | None = None


class ListPracticesInput(BaseModel):
    model_config = ConfigDict(strict=True)

    include_unapproved: bool = False


class ReviewPracticeInput(BaseModel):
    model_config = ConfigDict(strict=True)

    practice_id: UuidInput
    status: str = Field(pattern="^(PENDING|APPROVED|REJECTED)$")
    reviewed_by: str = Field(min_length=1, max_length=160)


class ApplicablePracticesInput(BaseModel):
    model_config = ConfigDict(strict=True)

    event: str
    stage: str
    changed_files: list[str] = Field(default_factory=list)
    component: str | None = None
    project_id: UuidInput | None = None
    actor_id: str | None = Field(default=None, max_length=160)
    organization_id: str | None = Field(default=None, max_length=160)
    context: dict[str, Any] = Field(default_factory=dict)
