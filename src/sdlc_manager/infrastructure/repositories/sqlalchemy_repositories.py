from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, sessionmaker

from ...domain.enums import EvidenceStatus, KnowledgeScope, MemoryType, ReviewStatus, WorkflowStatus
from ...domain.models import (
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
from ..database.db import session_scope
from ..database.models import (
    AuditRecord,
    EvaluationRecord,
    EventRecord,
    EvidenceRecord,
    ExceptionRecord,
    ExperienceRecord,
    GateRecord,
    PracticeRecord,
    ProjectRecord,
    SprintRecord,
    StageRecord,
    UserStoryRecord,
    WorkflowRecord,
)


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def encode(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def decode(value: str | None, fallback: Any) -> Any:
    if value is None:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


def project_from_record(record: ProjectRecord) -> Project:
    return Project(
        id=UUID(record.id),
        name=record.name,
        description=record.description,
        workflow_id=UUID(record.workflow_id) if record.workflow_id else None,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def sprint_from_record(record: SprintRecord) -> Sprint:
    return Sprint(
        id=UUID(record.id),
        project_id=UUID(record.project_id),
        name=record.name,
        start_date=record.start_date,
        end_date=record.end_date,
        status=record.status,
    )


def story_from_record(record: UserStoryRecord) -> UserStory:
    return UserStory(
        id=UUID(record.id),
        project_id=UUID(record.project_id),
        sprint_id=UUID(record.sprint_id) if record.sprint_id else None,
        external_reference=record.external_reference,
        title=record.title,
        description=record.description,
        acceptance_criteria=decode(record.acceptance_criteria, []),
        dependencies=decode(record.dependencies, []),
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def experience_from_record(record: ExperienceRecord) -> EngineeringExperience:
    return EngineeringExperience(
        id=UUID(record.id),
        title=record.title,
        context=record.context,
        problem=record.problem,
        root_cause=record.root_cause,
        solution=record.solution,
        lesson_learned=record.lesson_learned,
        component=record.component,
        tags=decode(record.tags, []),
        related_policy_ids=decode(record.related_policy_ids, []),
        review_status=ReviewStatus(record.review_status),
        created_at=record.created_at,
        memory_type=MemoryType(record.memory_type or MemoryType.LESSON_LEARNED),
        technology=record.technology,
        category=record.category,
        scope=KnowledgeScope(record.scope or KnowledgeScope.PERSONAL),
        project_id=UUID(record.project_id) if record.project_id else None,
        author=record.author,
        reviewed_by=record.reviewed_by,
        reviewed_at=record.reviewed_at,
        related_experience_ids=[UUID(item) for item in decode(record.related_experience_ids, [])],
    )


def evidence_from_record(record: EvidenceRecord) -> Evidence:
    return Evidence(
        id=UUID(record.id),
        project_id=UUID(record.project_id),
        user_story_id=UUID(record.user_story_id),
        policy_id=record.policy_id,
        evidence_type=record.evidence_type,
        reference=record.reference,
        verification_status=EvidenceStatus(record.verification_status),
        verified_by=record.verified_by,
        verified_at=record.verified_at,
        created_at=record.created_at,
    )


def event_from_record(record: EventRecord) -> ProcessedEvent:
    return ProcessedEvent(
        event_id=UUID(record.id),
        payload_hash=record.payload_hash,
        status=record.status,
        result=decode(record.result, {}),
        created_at=record.created_at,
    )


class SqlAlchemyProjectRepository:
    def __init__(self, factory: sessionmaker[Session]) -> None:
        self.factory = factory

    def save(self, project: Project) -> Project:
        now = project.updated_at or utc_now()
        record = ProjectRecord(
            id=str(project.id),
            name=project.name,
            description=project.description,
            workflow_id=str(project.workflow_id) if project.workflow_id else None,
            created_at=project.created_at or now,
            updated_at=now,
        )
        with session_scope(self.factory) as session:
            session.merge(record)
        return replace(project, created_at=record.created_at, updated_at=now)

    def get(self, project_id: UUID) -> Project | None:
        with session_scope(self.factory) as session:
            record = session.get(ProjectRecord, str(project_id))
            return project_from_record(record) if record else None

    def list_all(self) -> list[Project]:
        with session_scope(self.factory) as session:
            records = session.scalars(select(ProjectRecord)).all()
            return [project_from_record(item) for item in records]


class SqlAlchemySprintRepository:
    def __init__(self, factory: sessionmaker[Session]) -> None:
        self.factory = factory

    def save(self, sprint: Sprint) -> Sprint:
        record = SprintRecord(
            id=str(sprint.id),
            project_id=str(sprint.project_id),
            name=sprint.name,
            start_date=sprint.start_date,
            end_date=sprint.end_date,
            status=sprint.status,
        )
        with session_scope(self.factory) as session:
            session.merge(record)
        return sprint

    def list_by_project(self, project_id: UUID) -> list[Sprint]:
        with session_scope(self.factory) as session:
            records = session.scalars(
                select(SprintRecord).where(SprintRecord.project_id == str(project_id))
            ).all()
            return [sprint_from_record(item) for item in records]


class SqlAlchemyUserStoryRepository:
    def __init__(self, factory: sessionmaker[Session]) -> None:
        self.factory = factory

    def save(self, story: UserStory) -> UserStory:
        now = story.updated_at or utc_now()
        record = UserStoryRecord(
            id=str(story.id),
            project_id=str(story.project_id),
            sprint_id=str(story.sprint_id) if story.sprint_id else None,
            external_reference=story.external_reference,
            title=story.title,
            description=story.description,
            acceptance_criteria=encode(story.acceptance_criteria),
            dependencies=encode(story.dependencies),
            status=story.status,
            created_at=story.created_at or now,
            updated_at=now,
        )
        with session_scope(self.factory) as session:
            session.merge(record)
        return replace(story, created_at=record.created_at, updated_at=now)

    def get_for_project(self, project_id: UUID, story_id: UUID) -> UserStory | None:
        with session_scope(self.factory) as session:
            record = session.scalar(
                select(UserStoryRecord).where(
                    UserStoryRecord.id == str(story_id),
                    UserStoryRecord.project_id == str(project_id),
                )
            )
            return story_from_record(record) if record else None

    def list_by_project(self, project_id: UUID, sprint_id: UUID | None = None) -> list[UserStory]:
        with session_scope(self.factory) as session:
            statement = select(UserStoryRecord).where(UserStoryRecord.project_id == str(project_id))
            if sprint_id:
                statement = statement.where(UserStoryRecord.sprint_id == str(sprint_id))
            return [story_from_record(item) for item in session.scalars(statement).all()]


class SqlAlchemyExperienceRepository:
    def __init__(self, factory: sessionmaker[Session]) -> None:
        self.factory = factory

    def save(self, experience: EngineeringExperience) -> EngineeringExperience:
        record = ExperienceRecord(
            id=str(experience.id),
            title=experience.title,
            context=experience.context,
            problem=experience.problem,
            root_cause=experience.root_cause,
            solution=experience.solution,
            lesson_learned=experience.lesson_learned,
            component=experience.component,
            tags=encode(experience.tags),
            related_policy_ids=encode(experience.related_policy_ids),
            review_status=experience.review_status.value,
            created_at=experience.created_at or utc_now(),
            memory_type=experience.memory_type.value,
            technology=experience.technology,
            category=experience.category,
            scope=experience.scope.value,
            project_id=str(experience.project_id) if experience.project_id else None,
            author=experience.author,
            reviewed_by=experience.reviewed_by,
            reviewed_at=experience.reviewed_at,
            related_experience_ids=encode(
                [str(item) for item in experience.related_experience_ids]
            ),
        )
        with session_scope(self.factory) as session:
            session.merge(record)
        return replace(experience, created_at=record.created_at)

    def search(
        self,
        query: str | None = None,
        component: str | None = None,
        tags: list[str] | None = None,
        include_unreviewed: bool = False,
        project_id: UUID | None = None,
    ) -> list[EngineeringExperience]:
        with session_scope(self.factory) as session:
            statement = select(ExperienceRecord)
            if not include_unreviewed:
                statement = statement.where(
                    ExperienceRecord.review_status == ReviewStatus.APPROVED.value
                )
            if project_id:
                statement = statement.where(
                    (ExperienceRecord.scope != KnowledgeScope.PROJECT.value)
                    | (ExperienceRecord.project_id == str(project_id))
                )
            if component:
                statement = statement.where(ExperienceRecord.component == component)
            if query:
                term = f"%{query.lower()}%"
                statement = statement.where(
                    or_(
                        ExperienceRecord.title.ilike(term),
                        ExperienceRecord.context.ilike(term),
                        ExperienceRecord.problem.ilike(term),
                        ExperienceRecord.lesson_learned.ilike(term),
                        ExperienceRecord.tags.ilike(term),
                    )
                )
            records = session.scalars(statement).all()
            result = [experience_from_record(item) for item in records]
            if tags:
                result = [item for item in result if set(tags).intersection(item.tags)]
            return result

    def get(self, experience_id: UUID) -> EngineeringExperience | None:
        with session_scope(self.factory) as session:
            record = session.get(ExperienceRecord, str(experience_id))
            return experience_from_record(record) if record else None

    def save_review(
        self, experience_id: UUID, status: ReviewStatus, reviewed_by: str
    ) -> EngineeringExperience:
        experience = self.get(experience_id)
        if experience is None:
            raise ValueError("Experiencia no encontrada")
        return self.save(
            replace(
                experience,
                review_status=status,
                reviewed_by=reviewed_by,
                reviewed_at=utc_now(),
            )
        )


class SqlAlchemyEvidenceRepository:
    def __init__(self, factory: sessionmaker[Session]) -> None:
        self.factory = factory

    def save(self, evidence: Evidence) -> Evidence:
        record = EvidenceRecord(
            id=str(evidence.id),
            project_id=str(evidence.project_id),
            user_story_id=str(evidence.user_story_id),
            policy_id=evidence.policy_id,
            evidence_type=evidence.evidence_type,
            reference=evidence.reference,
            verification_status=evidence.verification_status.value,
            verified_by=evidence.verified_by,
            verified_at=evidence.verified_at,
            created_at=evidence.created_at or utc_now(),
        )
        with session_scope(self.factory) as session:
            session.merge(record)
        return replace(evidence, created_at=record.created_at)

    def get_for_project(self, project_id: UUID, evidence_id: UUID) -> Evidence | None:
        with session_scope(self.factory) as session:
            record = session.scalar(
                select(EvidenceRecord).where(
                    EvidenceRecord.id == str(evidence_id),
                    EvidenceRecord.project_id == str(project_id),
                )
            )
            return evidence_from_record(record) if record else None

    def list_for_story_and_policy(
        self, project_id: UUID, story_id: UUID | None, policy_id: str
    ) -> list[Evidence]:
        with session_scope(self.factory) as session:
            statement = select(EvidenceRecord).where(
                EvidenceRecord.project_id == str(project_id),
                EvidenceRecord.policy_id == policy_id,
            )
            if story_id:
                statement = statement.where(EvidenceRecord.user_story_id == str(story_id))
            return [evidence_from_record(item) for item in session.scalars(statement).all()]

    def list_for_story(self, project_id: UUID, story_id: UUID) -> list[Evidence]:
        with session_scope(self.factory) as session:
            records = session.scalars(
                select(EvidenceRecord).where(
                    EvidenceRecord.project_id == str(project_id),
                    EvidenceRecord.user_story_id == str(story_id),
                )
            ).all()
            return [evidence_from_record(item) for item in records]


class SqlAlchemyEvaluationRepository:
    def __init__(self, factory: sessionmaker[Session]) -> None:
        self.factory = factory

    def save(self, evaluation: PolicyEvaluation) -> PolicyEvaluation:
        record = EvaluationRecord(
            id=str(evaluation.id),
            project_id=str(evaluation.project_id),
            user_story_id=str(evaluation.user_story_id) if evaluation.user_story_id else None,
            gate=evaluation.gate,
            triggered_rule_ids=encode(evaluation.triggered_rule_ids),
            result=evaluation.result.value,
            missing_evidence=encode(evaluation.missing_evidence),
            explanation=evaluation.explanation,
            evaluated_at=evaluation.evaluated_at,
        )
        with session_scope(self.factory) as session:
            session.merge(record)
        return evaluation


def workflow_from_record(record: WorkflowRecord) -> SdlcWorkflow:
    return SdlcWorkflow(
        id=UUID(record.id),
        code=record.code,
        name=record.name,
        version=record.version,
        status=WorkflowStatus(record.status),
        source=record.source,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def stage_from_record(record: StageRecord) -> SdlcStage:
    return SdlcStage(
        id=UUID(record.id),
        workflow_id=UUID(record.workflow_id),
        code=record.code,
        name=record.name,
        description=record.description,
        order=record.order,
        required=record.required,
    )


def gate_from_record(record: GateRecord) -> SdlcGate:
    return SdlcGate(
        id=UUID(record.id),
        stage_id=UUID(record.stage_id),
        code=record.code,
        name=record.name,
        required=record.required,
        checks=decode(record.checks, []),
        conditions=decode(record.conditions, {}),
        enabled=record.enabled,
    )


def exception_from_record(record: ExceptionRecord) -> SdlcException:
    return SdlcException(
        id=UUID(record.id),
        workflow_id=UUID(record.workflow_id),
        gate_code=record.gate_code,
        code=record.code,
        reason=record.reason,
        condition=decode(record.condition, {}),
        status=ReviewStatus(record.status),
        approved_by=record.approved_by,
        approved_at=record.approved_at,
        responsible=record.responsible,
        valid_from=record.valid_from,
        valid_until=record.valid_until,
        approval_source=record.approval_source,
        approval_reference=record.approval_reference,
    )


def practice_from_record(record: PracticeRecord) -> EngineeringPractice:
    return EngineeringPractice(
        id=UUID(record.id),
        title=record.title,
        context=record.context,
        triggers=decode(record.triggers, {}),
        intervention_message=record.intervention_message,
        severity=record.severity,
        scope=KnowledgeScope(record.scope),
        project_id=UUID(record.project_id) if record.project_id else None,
        owner_id=record.owner_id,
        organization_id=record.organization_id,
        source_experience_id=UUID(record.source_experience_id)
        if record.source_experience_id
        else None,
        approval_status=ReviewStatus(record.approval_status),
        enabled=record.enabled,
        approved_by=record.approved_by,
        approved_at=record.approved_at,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


class SqlAlchemyWorkflowRepository:
    def __init__(self, factory: sessionmaker[Session]) -> None:
        self.factory = factory

    def save_workflow(self, workflow: SdlcWorkflow) -> SdlcWorkflow:
        now = workflow.updated_at or utc_now()
        record = WorkflowRecord(
            id=str(workflow.id),
            code=workflow.code,
            name=workflow.name,
            version=workflow.version,
            status=workflow.status.value,
            source=workflow.source,
            created_at=workflow.created_at or now,
            updated_at=now,
        )
        with session_scope(self.factory) as session:
            session.merge(record)
        return replace(workflow, created_at=record.created_at, updated_at=now)

    def save_stage(self, stage: SdlcStage) -> SdlcStage:
        record = StageRecord(
            id=str(stage.id),
            workflow_id=str(stage.workflow_id),
            code=stage.code,
            name=stage.name,
            description=stage.description,
            order=stage.order,
            required=stage.required,
        )
        with session_scope(self.factory) as session:
            session.merge(record)
        return stage

    def save_gate(self, gate: SdlcGate) -> SdlcGate:
        record = GateRecord(
            id=str(gate.id),
            stage_id=str(gate.stage_id),
            code=gate.code,
            name=gate.name,
            required=gate.required,
            checks=encode(gate.checks),
            conditions=encode(gate.conditions),
            enabled=gate.enabled,
        )
        with session_scope(self.factory) as session:
            session.merge(record)
        return gate

    def save_exception(self, exception: SdlcException) -> SdlcException:
        record = ExceptionRecord(
            id=str(exception.id),
            workflow_id=str(exception.workflow_id),
            gate_code=exception.gate_code,
            code=exception.code,
            reason=exception.reason,
            condition=encode(exception.condition),
            status=exception.status.value,
            approved_by=exception.approved_by,
            approved_at=exception.approved_at,
            responsible=exception.responsible,
            valid_from=exception.valid_from,
            valid_until=exception.valid_until,
            approval_source=exception.approval_source,
            approval_reference=exception.approval_reference,
        )
        with session_scope(self.factory) as session:
            session.merge(record)
        return exception

    def get(self, workflow_id: UUID) -> SdlcWorkflow | None:
        with session_scope(self.factory) as session:
            record = session.get(WorkflowRecord, str(workflow_id))
            return workflow_from_record(record) if record else None

    def get_by_code_version(self, code: str, version: str) -> SdlcWorkflow | None:
        with session_scope(self.factory) as session:
            record = session.scalar(
                select(WorkflowRecord).where(
                    WorkflowRecord.code == code,
                    WorkflowRecord.version == version,
                )
            )
            return workflow_from_record(record) if record else None

    def list_stages(self, workflow_id: UUID) -> list[SdlcStage]:
        with session_scope(self.factory) as session:
            records = session.scalars(
                select(StageRecord)
                .where(StageRecord.workflow_id == str(workflow_id))
                .order_by(StageRecord.order)
            ).all()
            return [stage_from_record(item) for item in records]

    def list_gates(self, workflow_id: UUID) -> list[SdlcGate]:
        with session_scope(self.factory) as session:
            records = session.scalars(
                select(GateRecord)
                .join(StageRecord, GateRecord.stage_id == StageRecord.id)
                .where(StageRecord.workflow_id == str(workflow_id))
            ).all()
            return [gate_from_record(item) for item in records]

    def list_exceptions(self, workflow_id: UUID) -> list[SdlcException]:
        with session_scope(self.factory) as session:
            records = session.scalars(
                select(ExceptionRecord).where(ExceptionRecord.workflow_id == str(workflow_id))
            ).all()
            return [exception_from_record(item) for item in records]


class SqlAlchemyPracticeRepository:
    def __init__(self, factory: sessionmaker[Session]) -> None:
        self.factory = factory

    def save(self, practice: EngineeringPractice) -> EngineeringPractice:
        now = practice.updated_at or utc_now()
        record = PracticeRecord(
            id=str(practice.id),
            title=practice.title,
            context=practice.context,
            triggers=encode(practice.triggers),
            intervention_message=practice.intervention_message,
            severity=practice.severity,
            scope=practice.scope.value,
            project_id=str(practice.project_id) if practice.project_id else None,
            owner_id=practice.owner_id,
            organization_id=practice.organization_id,
            source_experience_id=str(practice.source_experience_id)
            if practice.source_experience_id
            else None,
            approval_status=practice.approval_status.value,
            enabled=practice.enabled,
            approved_by=practice.approved_by,
            approved_at=practice.approved_at,
            created_at=practice.created_at or now,
            updated_at=now,
        )
        with session_scope(self.factory) as session:
            session.merge(record)
        return replace(practice, created_at=record.created_at, updated_at=now)

    def list(self, include_unapproved: bool = False) -> list[EngineeringPractice]:
        with session_scope(self.factory) as session:
            statement = select(PracticeRecord)
            if not include_unapproved:
                statement = statement.where(
                    PracticeRecord.approval_status == ReviewStatus.APPROVED.value
                )
            return [practice_from_record(item) for item in session.scalars(statement).all()]

    def get(self, practice_id: UUID) -> EngineeringPractice | None:
        with session_scope(self.factory) as session:
            record = session.get(PracticeRecord, str(practice_id))
            return practice_from_record(record) if record else None

    def save_review(
        self, practice_id: UUID, status: ReviewStatus, reviewed_by: str
    ) -> EngineeringPractice:
        practice = self.get(practice_id)
        if practice is None:
            raise ValueError("Practica no encontrada")
        return self.save(
            replace(
                practice,
                approval_status=status,
                approved_by=reviewed_by if status == ReviewStatus.APPROVED else None,
                approved_at=utc_now() if status == ReviewStatus.APPROVED else None,
            )
        )


class SqlAlchemyAuditRepository:
    def __init__(self, factory: sessionmaker[Session]) -> None:
        self.factory = factory

    def save(self, entry: AuditEntry) -> AuditEntry:
        record = AuditRecord(
            event_type=entry.event_type,
            project_id=str(entry.project_id) if entry.project_id else None,
            entity_id=entry.entity_id,
            details=encode(entry.details),
            created_at=entry.created_at or utc_now(),
        )
        with session_scope(self.factory) as session:
            session.add(record)
            session.flush()
        return replace(entry, created_at=record.created_at)


class SqlAlchemyEventRepository:
    def __init__(self, factory: sessionmaker[Session]) -> None:
        self.factory = factory

    def get(self, event_id: UUID) -> ProcessedEvent | None:
        with session_scope(self.factory) as session:
            record = session.get(EventRecord, str(event_id))
            return event_from_record(record) if record else None

    def save(self, event: ProcessedEvent) -> ProcessedEvent:
        record = EventRecord(
            id=str(event.event_id),
            payload_hash=event.payload_hash,
            status=event.status,
            result=encode(event.result),
            created_at=event.created_at or utc_now(),
        )
        with session_scope(self.factory) as session:
            session.merge(record)
        return replace(event, created_at=record.created_at)
