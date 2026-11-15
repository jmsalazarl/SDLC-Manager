from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa

from sdlc_manager.application.event_schemas import SdlcEvent
from sdlc_manager.config import Settings
from sdlc_manager.domain.enums import (
    EvaluationResult,
    EventProcessingStatus,
    KnowledgeScope,
    ReviewStatus,
)
from sdlc_manager.infrastructure.container import build_container


def make_event(
    event_type: str,
    *,
    event_id: UUID | None = None,
    project_id: UUID | None = None,
    user_story_id: UUID | None = None,
    affected_files: list[str] | None = None,
    context: dict | None = None,
) -> SdlcEvent:
    return SdlcEvent.model_validate(
        {
            "event_id": str(event_id or uuid4()),
            "event_type": event_type,
            "source_client": "test-client",
            "project_id": str(project_id) if project_id else None,
            "user_story_id": str(user_story_id) if user_story_id else None,
            "timestamp": datetime.now(UTC).isoformat(),
            "affected_files": affected_files or [],
            "context": context or {},
        }
    )


def test_valid_file_event_detects_forms_policy(container) -> None:
    project = container.service.create_project("Event project")
    event = make_event(
        "file_changed",
        project_id=project.id,
        affected_files=["formularios/Pagos.wpx"],
    )

    result = container.event_processor.process(event)

    assert result.status == EventProcessingStatus.PROCESSED
    assert result.decision is None
    assert "SDLC-001" in result.triggered_rules


def test_contextual_practice_returns_warning_without_block(container) -> None:
    project = container.service.create_project("Practice event project")
    practice = container.service.register_practice(
        title="Revisar feature flags",
        context="Cambio critico",
        triggers={"event": "file_change", "components": ["payments"]},
        intervention_message="Revisar feature flags",
        severity="MEDIUM",
        scope=KnowledgeScope.PROJECT,
        project_id=project.id,
    )
    container.service.review_practice(practice.id, ReviewStatus.APPROVED, "reviewer")
    event = make_event(
        "file_changed",
        project_id=project.id,
        context={"component": "payments"},
    )

    result = container.event_processor.process(event)

    assert result.decision == EvaluationResult.WARN
    assert result.applicable_practices == [str(practice.id)]


def test_event_context_respects_project_isolation_and_finds_experience(container) -> None:
    first = container.service.create_project("First event project")
    second = container.service.create_project("Second event project")
    experience = container.service.register_experience(
        title="Incident de pagos",
        context="Componente de pagos",
        problem="Consulta lenta",
        root_cause="Indice ausente",
        solution="Agregar indice",
        lesson_learned="Medir antes y despues",
        component="payments",
        tags=["performance"],
        related_policy_ids=[],
        scope="PROJECT",
        project_id=first.id,
        author="reviewer",
    )
    container.service.review_experience(experience.id, ReviewStatus.APPROVED, "reviewer")
    practice = container.service.register_practice(
        title="Project recommendation",
        context="First project",
        triggers={"event": "file_change"},
        intervention_message="Review first project",
        severity="LOW",
        scope=KnowledgeScope.PROJECT,
        project_id=first.id,
    )
    container.service.review_practice(practice.id, ReviewStatus.APPROVED, "reviewer")

    first_result = container.event_processor.process(
        make_event(
            "file_changed",
            project_id=first.id,
            context={"component": "payments", "experience_query": "pagos"},
        )
    )
    second_result = container.event_processor.process(
        make_event(
            "file_changed",
            project_id=second.id,
            context={"component": "payments", "experience_query": "pagos"},
        )
    )

    assert first_result.applicable_practices == [str(practice.id)]
    assert second_result.applicable_practices == []
    assert first_result.relevant_experiences == [str(experience.id)]
    assert second_result.relevant_experiences == []


def test_incomplete_story_event_blocks(container) -> None:
    project = container.service.create_project("Incomplete story project")
    story = container.service.create_story(project.id, "Incomplete", description=None)
    event = make_event(
        "user_story_started",
        project_id=project.id,
        user_story_id=story.id,
    )

    result = container.event_processor.process(event)

    assert result.status == EventProcessingStatus.PROCESSED
    assert result.decision == EvaluationResult.BLOCK
    assert result.workflow_checks == ["story_ready"]


def test_pending_then_verified_gate_event_matches_current_engine(container) -> None:
    project = container.service.create_project("Evidence event project")
    story = container.service.create_story(project.id, "Complete", description="Description")
    pending_event = make_event(
        "task_completed",
        project_id=project.id,
        user_story_id=story.id,
    )

    blocked = container.event_processor.process(pending_event)
    evidence = container.service.register_evidence(
        project.id, story.id, "WORKFLOW", "closure_evidence", "record:closure"
    )
    pending = container.event_processor.process(
        make_event("task_completed", project_id=project.id, user_story_id=story.id)
    )
    container.service.verify_evidence(project.id, evidence.id, "human-reviewer")
    passed = container.event_processor.process(
        make_event("task_completed", project_id=project.id, user_story_id=story.id)
    )

    assert blocked.decision == EvaluationResult.BLOCK
    assert pending.decision == EvaluationResult.BLOCK
    assert passed.decision == EvaluationResult.PASS


def test_duplicate_and_conflicting_event_id_do_not_repeat_audit(container) -> None:
    event = make_event("session_started")
    first = container.event_processor.process(event)
    duplicate = container.event_processor.process(event)
    conflict = container.event_processor.process(
        make_event("session_started", event_id=event.event_id, context={"different": True})
    )
    engine = container.service.projects.factory.kw["bind"]
    with engine.connect() as connection:
        event_count = connection.execute(sa.text("SELECT COUNT(*) FROM TEVENTOSDLC")).scalar_one()
        audit_count = connection.execute(
            sa.text("SELECT COUNT(*) FROM TAUDITORIA WHERE TIPOEVENTO = 'sdlc_event_processed'")
        ).scalar_one()

    assert first.status == EventProcessingStatus.PROCESSED
    assert duplicate.status == EventProcessingStatus.DUPLICATE
    assert duplicate.explanation == first.explanation
    assert conflict.status == EventProcessingStatus.REJECTED
    assert conflict.error_code == "EVENT_ID_REUSED"
    assert event_count == 1
    assert audit_count == 1


def test_invalid_uuid_and_missing_required_project_are_rejected(container) -> None:
    invalid_uuid = container.event_processor.process_payload(
        {
            "event_id": "not-a-uuid",
            "event_type": "file_changed",
            "source_client": "test-client",
            "project_id": "not-a-uuid",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )
    missing_project = container.event_processor.process_payload(
        {
            "event_id": str(uuid4()),
            "event_type": "file_changed",
            "source_client": "test-client",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )

    assert invalid_uuid.status == EventProcessingStatus.REJECTED
    assert invalid_uuid.error_code == "INVALID_EVENT"
    assert missing_project.status == EventProcessingStatus.REJECTED
    assert missing_project.error_code == "INVALID_EVENT"


def test_unknown_event_is_structured_as_unsupported(container) -> None:
    event_id = uuid4()
    result = container.event_processor.process_payload(
        {
            "event_id": str(event_id),
            "event_type": "future_event",
            "source_client": "test-client",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )

    assert result.status == EventProcessingStatus.UNSUPPORTED
    assert result.error_code == "UNSUPPORTED_EVENT_TYPE"
    assert result.decision is None


def test_unexpected_error_is_not_pass(monkeypatch: pytest.MonkeyPatch, container) -> None:
    project = container.service.create_project("Error project")

    def fail(*args: object, **kwargs: object) -> list[dict]:
        raise RuntimeError("unexpected")

    monkeypatch.setattr(container.service, "get_applicable_rules", fail)
    result = container.event_processor.process(make_event("file_changed", project_id=project.id))

    assert result.status == EventProcessingStatus.ERROR
    assert result.error_code == "PROCESSING_ERROR"
    assert result.retryable is True
    assert result.decision is None


def test_event_result_survives_container_restart(container, tmp_path: Path) -> None:
    event = make_event("session_started")
    first = container.event_processor.process(event)
    engine = container.service.projects.factory.kw["bind"]
    root = Path(__file__).parents[2]
    settings = Settings(
        database_url=str(engine.url),
        policy_paths=[str(root / "knowledge" / "rules")],
        project_root=root,
    )
    restarted = build_container(settings)

    duplicate = restarted.event_processor.process(event)

    assert first.status == EventProcessingStatus.PROCESSED
    assert duplicate.status == EventProcessingStatus.DUPLICATE
    assert duplicate.event_id == event.event_id
