from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator, model_validator

from ..domain.enums import EvaluationResult, EventProcessingStatus, SdlcEventType
from .schemas import UuidInput


def parse_utc_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        timestamp = value
    elif isinstance(value, str):
        try:
            timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("timestamp debe ser una fecha ISO valida") from error
    else:
        raise ValueError("timestamp debe ser una fecha ISO")
    if timestamp.tzinfo is None:
        raise ValueError("timestamp debe incluir zona horaria UTC")
    return timestamp.astimezone(UTC)


type UtcTimestampInput = Annotated[datetime, BeforeValidator(parse_utc_timestamp)]


def parse_event_type(value: Any) -> SdlcEventType:
    if isinstance(value, SdlcEventType):
        return value
    if isinstance(value, str):
        try:
            return SdlcEventType(value)
        except ValueError as error:
            raise ValueError("event_type no esta soportado") from error
    raise ValueError("event_type debe ser texto")


type EventTypeInput = Annotated[SdlcEventType, BeforeValidator(parse_event_type)]


def parse_processing_status(value: Any) -> EventProcessingStatus:
    if isinstance(value, EventProcessingStatus):
        return value
    if isinstance(value, str):
        try:
            return EventProcessingStatus(value)
        except ValueError as error:
            raise ValueError("status no esta soportado") from error
    raise ValueError("status debe ser texto")


type ProcessingStatusInput = Annotated[
    EventProcessingStatus, BeforeValidator(parse_processing_status)
]


def parse_decision(value: Any) -> EvaluationResult | None:
    if value is None or isinstance(value, EvaluationResult):
        return value
    if isinstance(value, str):
        try:
            return EvaluationResult(value)
        except ValueError as error:
            raise ValueError("decision no esta soportada") from error
    raise ValueError("decision debe ser texto o null")


type DecisionInput = Annotated[EvaluationResult | None, BeforeValidator(parse_decision)]


def _validate_json_value(value: Any, depth: int = 0) -> None:
    if depth > 5:
        raise ValueError("context tiene una profundidad maxima de 5 niveles")
    if value is None or isinstance(value, str | int | bool):
        if isinstance(value, str) and len(value) > 2000:
            raise ValueError("los valores de context no pueden superar 2000 caracteres")
        return
    if isinstance(value, float):
        return
    if isinstance(value, list):
        if len(value) > 100:
            raise ValueError("las listas de context no pueden superar 100 elementos")
        for item in value:
            _validate_json_value(item, depth + 1)
        return
    if isinstance(value, dict):
        if len(value) > 64:
            raise ValueError("context no puede superar 64 claves")
        for key, item in value.items():
            if not isinstance(key, str) or not key or len(key) > 100:
                raise ValueError("las claves de context deben ser texto acotado")
            _validate_json_value(item, depth + 1)
        return
    raise ValueError("context solo admite valores JSON")


class SdlcEvent(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    event_id: UuidInput
    event_type: EventTypeInput
    source_client: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9._-]+$")
    project_id: UuidInput | None = None
    user_story_id: UuidInput | None = None
    stage: str | None = Field(default=None, min_length=1, max_length=80)
    timestamp: UtcTimestampInput
    affected_files: list[str] = Field(default_factory=list, max_length=100)
    context: dict[str, Any] = Field(default_factory=dict)
    schema_version: str = Field(default="1.0", pattern=r"^1\.0$")

    @field_validator("affected_files")
    @classmethod
    def validate_files(cls, files: list[str]) -> list[str]:
        for path in files:
            if not path or len(path) > 500:
                raise ValueError("cada archivo debe tener entre 1 y 500 caracteres")
            if path.startswith(("/", "\\")) or ".." in path.replace("\\", "/").split("/"):
                raise ValueError("las rutas afectadas no pueden ser absolutas ni contener ..")
        return files

    @field_validator("context")
    @classmethod
    def validate_context(cls, context: dict[str, Any]) -> dict[str, Any]:
        _validate_json_value(context)
        return context

    @model_validator(mode="after")
    def validate_scope(self) -> SdlcEvent:
        requires_project = {
            SdlcEventType.SPRINT_STARTED,
            SdlcEventType.USER_STORY_STARTED,
            SdlcEventType.SDD_TASK_STARTED,
            SdlcEventType.FILE_CHANGED,
            SdlcEventType.TASK_COMPLETED,
            SdlcEventType.GATE_EVALUATION_REQUESTED,
            SdlcEventType.INCIDENT_RECORDED,
        }
        requires_story = {
            SdlcEventType.USER_STORY_STARTED,
            SdlcEventType.SDD_TASK_STARTED,
            SdlcEventType.TASK_COMPLETED,
            SdlcEventType.GATE_EVALUATION_REQUESTED,
        }
        if self.event_type in requires_project and self.project_id is None:
            raise ValueError("project_id es obligatorio para este evento")
        if self.event_type in requires_story and self.user_story_id is None:
            raise ValueError("user_story_id es obligatorio para este evento")
        return self


class EventProcessingResult(BaseModel):
    model_config = ConfigDict(strict=True)

    event_id: UuidInput | None = None
    status: ProcessingStatusInput
    decision: DecisionInput = None
    triggered_rules: list[str] = Field(default_factory=list)
    workflow_checks: list[str] = Field(default_factory=list)
    applicable_practices: list[str] = Field(default_factory=list)
    relevant_experiences: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list, max_length=10)
    missing_evidence: list[str] = Field(default_factory=list)
    explanation: str
    error_code: str | None = None
    retryable: bool = False
    processed_at: UtcTimestampInput
    sddnxp_context: dict[str, Any] | None = None
