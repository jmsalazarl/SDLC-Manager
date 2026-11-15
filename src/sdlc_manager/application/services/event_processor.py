from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import ValidationError

from ...domain.enums import EvaluationResult, EventProcessingStatus, SdlcEventType
from ...domain.models import AuditEntry, ProcessedEvent
from ...domain.ports.repositories import AuditRepository, EventRepository
from ...engines.experience_engine import ExperienceEngine
from ..event_schemas import EventProcessingResult, SdlcEvent
from .sdlc_service import ApplicationError, SdlcService


class SdlcEventProcessor:
    """Coordina eventos normalizados sin depender de un cliente externo."""

    def __init__(
        self,
        service: SdlcService,
        events: EventRepository,
        audits: AuditRepository,
    ) -> None:
        self.service = service
        self.events = events
        self.audits = audits
        self.experience_engine = ExperienceEngine(service.experiences)

    def process_payload(self, payload: object) -> EventProcessingResult:
        try:
            event = SdlcEvent.model_validate(payload)
        except ValidationError as error:
            return self._invalid_payload_result(payload, error)
        return self.process(event)

    def process(self, event: SdlcEvent) -> EventProcessingResult:
        payload_hash = self._payload_hash(event.model_dump(mode="json"))
        previous = self.events.get(event.event_id)
        if previous is not None:
            if previous.payload_hash != payload_hash:
                return self._result(
                    event.event_id,
                    EventProcessingStatus.REJECTED,
                    "El event_id ya fue utilizado con un payload diferente",
                    error_code="EVENT_ID_REUSED",
                )
            return EventProcessingResult.model_validate(previous.result).model_copy(
                update={"status": EventProcessingStatus.DUPLICATE}
            )

        try:
            result = self._dispatch(event)
        except ApplicationError as error:
            result = self._result(
                event.event_id,
                EventProcessingStatus.ERROR,
                str(error),
                error_code="APPLICATION_ERROR",
                retryable=False,
            )
        except Exception:
            result = self._result(
                event.event_id,
                EventProcessingStatus.ERROR,
                "Ocurrio un error inesperado durante el procesamiento",
                error_code="PROCESSING_ERROR",
                retryable=True,
            )

        self._persist(event, payload_hash, result)
        return result

    def _dispatch(self, event: SdlcEvent) -> EventProcessingResult:
        if event.event_type == SdlcEventType.SESSION_STARTED:
            return self._result(
                event.event_id,
                EventProcessingStatus.PROCESSED,
                "Sesion registrada sin evaluacion de gate",
            )

        if event.event_type == SdlcEventType.SPRINT_STARTED:
            summary = self.service.start_sprint(
                self._project_id(event), self._context_uuid(event.context, "sprint_id")
            )
            risks = int(summary["total_stories"]) - int(summary["ready_stories"])
            return self._result(
                event.event_id,
                EventProcessingStatus.PROCESSED,
                f"Sprint analizado: {summary['total_stories']} historias, {risks} con riesgos",
                decision=EvaluationResult.WARN if risks else None,
            )

        rules, practices, experiences = self._contextual_findings(event)
        if event.event_type == SdlcEventType.USER_STORY_STARTED:
            analysis = self.service.analyze_user_story(
                self._project_id(event), self._story_id(event)
            )
            decision = (
                EvaluationResult.PASS
                if analysis["ready_for_development"]
                else EvaluationResult.BLOCK
            )
            return self._result(
                event.event_id,
                EventProcessingStatus.PROCESSED,
                (
                    "HU lista para desarrollo"
                    if decision == EvaluationResult.PASS
                    else "HU incompleta"
                ),
                decision=decision,
                triggered_rules=[item["id"] for item in analysis["applicable_rules"]],
                workflow_checks=["story_ready"],
                applicable_practices=practices,
                relevant_experiences=experiences,
            )

        if event.event_type == SdlcEventType.SDD_TASK_STARTED and "gate" not in event.context:
            analysis = self.service.analyze_user_story(
                self._project_id(event), self._story_id(event)
            )
            decision = (
                EvaluationResult.PASS
                if analysis["ready_for_development"]
                else EvaluationResult.BLOCK
            )
            return self._result(
                event.event_id,
                EventProcessingStatus.PROCESSED,
                "Tarea SDD lista" if decision == EvaluationResult.PASS else "HU incompleta",
                decision=decision,
                triggered_rules=[item["id"] for item in analysis["applicable_rules"]],
                workflow_checks=["story_ready"],
                applicable_practices=practices,
                relevant_experiences=experiences,
            )

        if event.event_type in {
            SdlcEventType.SDD_TASK_STARTED,
            SdlcEventType.TASK_COMPLETED,
            SdlcEventType.GATE_EVALUATION_REQUESTED,
        }:
            gate = self._gate_for(event)
            gate_result = self.service.evaluate_gate(
                self._project_id(event),
                self._story_id(event),
                gate,
                self._service_context(event),
            )
            return self._result(
                event.event_id,
                EventProcessingStatus.PROCESSED,
                gate_result["explanation"],
                decision=EvaluationResult(gate_result["result"]),
                triggered_rules=gate_result["triggered_rules"],
                workflow_checks=[
                    item["check"]
                    for item in gate_result["workflow_findings"]
                    if isinstance(item, dict) and isinstance(item.get("check"), str)
                ],
                applicable_practices=practices,
                relevant_experiences=experiences,
                missing_evidence=gate_result["missing_evidence"],
            )

        return self._result(
            event.event_id,
            EventProcessingStatus.PROCESSED,
            "Evento procesado sin evaluacion de gate",
            decision=EvaluationResult.WARN if practices else None,
            triggered_rules=[item["id"] for item in rules],
            applicable_practices=practices,
            relevant_experiences=experiences,
        )

    def _contextual_findings(
        self, event: SdlcEvent
    ) -> tuple[list[dict[str, Any]], list[str], list[str]]:
        if event.project_id is None:
            return [], [], []
        context = self._service_context(event)
        rules = self.service.get_applicable_rules(
            project_id=event.project_id,
            user_story_id=event.user_story_id,
            event=self._policy_event(event),
            stage=event.stage or event.event_type.value,
            changed_files=event.affected_files,
            component=self._context_text(event.context, "component"),
            context=context,
        )
        practices = self.service.get_applicable_practices(context)
        query = self._context_text(event.context, "experience_query")
        component = self._context_text(event.context, "component")
        tags = self._context_tags(event.context, "experience_tags")
        experiences = []
        if query or component or tags:
            experiences = self.experience_engine.search(
                query, component, tags, project_id=event.project_id
            )
        return rules, [str(item.id) for item in practices], [str(item.id) for item in experiences]

    @staticmethod
    def _project_id(event: SdlcEvent) -> UUID:
        if event.project_id is None:
            raise ApplicationError("project_id es obligatorio para este evento")
        return event.project_id

    @staticmethod
    def _story_id(event: SdlcEvent) -> UUID:
        if event.user_story_id is None:
            raise ApplicationError("user_story_id es obligatorio para este evento")
        return event.user_story_id

    @staticmethod
    def _service_context(event: SdlcEvent) -> dict[str, Any]:
        context = dict(event.context)
        context.update(
            {
                "event": SdlcEventProcessor._policy_event(event),
                "stage": event.stage or event.event_type.value,
                "changed_files": event.affected_files,
                "project_id": str(event.project_id) if event.project_id else None,
                "user_story_id": str(event.user_story_id) if event.user_story_id else None,
            }
        )
        return context

    @staticmethod
    def _policy_event(event: SdlcEvent) -> str:
        if event.event_type == SdlcEventType.FILE_CHANGED:
            return "file_change"
        return event.event_type.value

    @staticmethod
    def _gate_for(event: SdlcEvent) -> str:
        gate = event.context.get("gate")
        if gate is None and event.event_type == SdlcEventType.TASK_COMPLETED:
            return "task_completion"
        if not isinstance(gate, str) or not gate:
            raise ApplicationError("context.gate es obligatorio para este evento")
        return gate

    @staticmethod
    def _context_uuid(context: dict[str, Any], key: str) -> UUID | None:
        value = context.get(key)
        if value is None:
            return None
        if not isinstance(value, str):
            raise ApplicationError(f"context.{key} debe ser UUID serializado")
        try:
            return UUID(value)
        except ValueError as error:
            raise ApplicationError(f"context.{key} no es un UUID valido") from error

    @staticmethod
    def _context_text(context: dict[str, Any], key: str) -> str | None:
        value = context.get(key)
        if value is None:
            return None
        if not isinstance(value, str) or not value:
            raise ApplicationError(f"context.{key} debe ser texto no vacio")
        return value

    @staticmethod
    def _context_tags(context: dict[str, Any], key: str) -> list[str]:
        value = context.get(key, [])
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ApplicationError(f"context.{key} debe ser una lista de textos")
        return value

    def _persist(self, event: SdlcEvent, payload_hash: str, result: EventProcessingResult) -> None:
        self.events.save(
            ProcessedEvent(
                event_id=event.event_id,
                payload_hash=payload_hash,
                status=result.status.value,
                result=result.model_dump(mode="json"),
            )
        )
        self.audits.save(
            AuditEntry(
                event_type="sdlc_event_processed",
                project_id=event.project_id,
                entity_id=str(event.event_id),
                details={
                    "event_type": event.event_type.value,
                    "status": result.status.value,
                    "decision": result.decision.value if result.decision else None,
                    "error_code": result.error_code,
                },
            )
        )

    def _invalid_payload_result(
        self, payload: object, error: ValidationError
    ) -> EventProcessingResult:
        event_id = self._extract_uuid(payload, "event_id")
        event_type = payload.get("event_type") if isinstance(payload, dict) else None
        if isinstance(event_type, str) and event_type not in {item.value for item in SdlcEventType}:
            result = self._result(
                event_id,
                EventProcessingStatus.UNSUPPORTED,
                "El tipo de evento no esta soportado",
                error_code="UNSUPPORTED_EVENT_TYPE",
            )
        else:
            result = self._result(
                event_id,
                EventProcessingStatus.REJECTED,
                "El evento no cumple el contrato de entrada",
                error_code="INVALID_EVENT",
            )
        if event_id is not None and result.status == EventProcessingStatus.UNSUPPORTED:
            try:
                raw_hash = self._payload_hash(payload)
            except (TypeError, ValueError):
                return result
            previous = self.events.get(event_id)
            if previous is not None:
                if previous.payload_hash != raw_hash:
                    return self._result(
                        event_id,
                        EventProcessingStatus.REJECTED,
                        "El event_id ya fue utilizado con un payload diferente",
                        error_code="EVENT_ID_REUSED",
                    )
                return EventProcessingResult.model_validate(previous.result).model_copy(
                    update={"status": EventProcessingStatus.DUPLICATE}
                )
            self.events.save(
                ProcessedEvent(
                    event_id=event_id,
                    payload_hash=raw_hash,
                    status=result.status.value,
                    result=result.model_dump(mode="json"),
                )
            )
            self.audits.save(
                AuditEntry(
                    event_type="sdlc_event_processed",
                    project_id=None,
                    entity_id=str(event_id),
                    details={"status": result.status.value, "error_code": result.error_code},
                )
            )
        _ = error
        return result

    @staticmethod
    def _extract_uuid(payload: object, key: str) -> UUID | None:
        if not isinstance(payload, dict):
            return None
        value = payload.get(key)
        if isinstance(value, UUID):
            return value
        if isinstance(value, str):
            try:
                return UUID(value)
            except ValueError:
                return None
        return None

    @staticmethod
    def _payload_hash(payload: object) -> str:
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    @staticmethod
    def _result(
        event_id: UUID | None,
        status: EventProcessingStatus,
        explanation: str,
        *,
        decision: EvaluationResult | None = None,
        triggered_rules: list[str] | None = None,
        workflow_checks: list[str] | None = None,
        applicable_practices: list[str] | None = None,
        relevant_experiences: list[str] | None = None,
        missing_evidence: list[str] | None = None,
        error_code: str | None = None,
        retryable: bool = False,
    ) -> EventProcessingResult:
        return EventProcessingResult(
            event_id=event_id,
            status=status,
            decision=decision,
            triggered_rules=triggered_rules or [],
            workflow_checks=workflow_checks or [],
            applicable_practices=applicable_practices or [],
            relevant_experiences=relevant_experiences or [],
            missing_evidence=missing_evidence or [],
            explanation=explanation,
            error_code=error_code,
            retryable=retryable,
            processed_at=datetime.now(UTC),
        )
