from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any
from uuid import UUID

from .enums import (
    EvaluationResult,
    EvidenceStatus,
    KnowledgeScope,
    MemoryType,
    PolicyApprovalStatus,
    ReviewStatus,
    WorkflowStatus,
)


@dataclass(frozen=True, slots=True)
class Project:
    id: UUID
    name: str
    description: str | None = None
    workflow_id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Sprint:
    id: UUID
    project_id: UUID
    name: str
    start_date: date | None = None
    end_date: date | None = None
    status: str = "PLANNED"


@dataclass(frozen=True, slots=True)
class UserStory:
    id: UUID
    project_id: UUID
    sprint_id: UUID | None
    external_reference: str | None
    title: str
    description: str | None
    acceptance_criteria: list[str]
    dependencies: list[dict[str, Any]]
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class PolicyRule:
    id: str
    name: str
    description: str
    version: str
    severity: str
    trigger: dict[str, Any]
    scope: dict[str, Any]
    conditions: dict[str, Any]
    required_evidence: list[str]
    target_gate: str
    action: str
    approval_status: PolicyApprovalStatus
    workflow_checks: list[str] = field(default_factory=list)
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class EngineeringExperience:
    id: UUID
    title: str
    context: str
    problem: str
    root_cause: str
    solution: str
    lesson_learned: str
    component: str | None
    tags: list[str]
    related_policy_ids: list[str]
    review_status: ReviewStatus
    created_at: datetime | None = None
    memory_type: MemoryType = MemoryType.LESSON_LEARNED
    technology: str | None = None
    category: str | None = None
    scope: KnowledgeScope = KnowledgeScope.PERSONAL
    project_id: UUID | None = None
    author: str | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    related_experience_ids: list[UUID] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class SdlcWorkflow:
    id: UUID
    code: str
    name: str
    version: str
    status: WorkflowStatus
    source: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class SdlcStage:
    id: UUID
    workflow_id: UUID
    code: str
    name: str
    description: str
    order: int
    required: bool


@dataclass(frozen=True, slots=True)
class SdlcGate:
    id: UUID
    stage_id: UUID
    code: str
    name: str
    required: bool
    checks: list[str]
    conditions: dict[str, Any]
    enabled: bool


@dataclass(frozen=True, slots=True)
class SdlcException:
    id: UUID
    workflow_id: UUID
    gate_code: str
    code: str
    reason: str
    condition: dict[str, Any]
    status: ReviewStatus
    approved_by: str | None = None
    approved_at: datetime | None = None
    responsible: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    approval_source: str | None = None
    approval_reference: str | None = None


@dataclass(frozen=True, slots=True)
class EngineeringPractice:
    id: UUID
    title: str
    context: str
    triggers: dict[str, Any]
    intervention_message: str
    severity: str
    scope: KnowledgeScope
    source_experience_id: UUID | None
    approval_status: ReviewStatus
    project_id: UUID | None = None
    owner_id: str | None = None
    organization_id: str | None = None
    enabled: bool = True
    approved_by: str | None = None
    approved_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Evidence:
    id: UUID
    project_id: UUID
    user_story_id: UUID
    policy_id: str
    evidence_type: str
    reference: str
    verification_status: EvidenceStatus
    verified_by: str | None
    verified_at: datetime | None
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class PolicyEvaluation:
    id: UUID
    project_id: UUID
    user_story_id: UUID | None
    gate: str
    triggered_rule_ids: list[str]
    result: EvaluationResult
    missing_evidence: list[str]
    explanation: str
    evaluated_at: datetime


@dataclass(frozen=True, slots=True)
class GateDecision:
    evaluation_id: UUID
    result: EvaluationResult
    gate: str
    triggered_rules: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    explanation: str = ""
    evaluated_at: datetime | None = None
    pending_evidence: list[str] = field(default_factory=list)
    rejected_evidence: list[str] = field(default_factory=list)
    not_applicable_checks: list[str] = field(default_factory=list)
    workflow_findings: list[dict[str, Any]] = field(default_factory=list)
    evaluation_errors: list[str] = field(default_factory=list)
    deduplicated_policy_rules: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class AuditEntry:
    event_type: str
    project_id: UUID | None
    entity_id: str | None
    details: dict[str, Any]
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ProcessedEvent:
    event_id: UUID
    payload_hash: str
    status: str
    result: dict[str, Any]
    created_at: datetime | None = None
