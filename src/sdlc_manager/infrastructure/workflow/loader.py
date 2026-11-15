from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ...domain.enums import ReviewStatus, WorkflowStatus
from ...domain.models import SdlcException, SdlcGate, SdlcStage, SdlcWorkflow
from ...domain.ports.repositories import ProjectRepository, WorkflowRepository


class WorkflowLoadError(ValueError):
    """Indica que una plantilla SDLC no cumple su contrato."""


class WorkflowGateYaml(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=200)
    required: bool = True
    checks: list[str] = Field(default_factory=list)
    conditions: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class WorkflowStageYaml(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    order: int = Field(ge=1)
    required: bool = True
    gates: list[WorkflowGateYaml] = Field(default_factory=list)


class WorkflowExceptionYaml(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    gate_code: str = Field(min_length=1, max_length=80)
    code: str = Field(min_length=1, max_length=80)
    reason: str = Field(min_length=1)
    condition: dict[str, Any] = Field(default_factory=dict)
    responsible: str | None = Field(default=None, max_length=160)
    valid_from: str | None = None
    valid_until: str | None = None
    approval_source: str | None = Field(default=None, max_length=160)
    approval_reference: str | None = Field(default=None, max_length=200)


class WorkflowYaml(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=200)
    version: str = Field(min_length=1, max_length=40)
    status: str = Field(pattern="^(DRAFT|ACTIVE|ARCHIVED)$")
    source: str = Field(min_length=1, max_length=200)
    stages: list[WorkflowStageYaml] = Field(min_length=1)
    exceptions: list[WorkflowExceptionYaml] = Field(default_factory=list)


def load_workflow(path: Path) -> WorkflowYaml:
    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(content, dict):
            raise WorkflowLoadError(f"El archivo {path} debe contener un objeto YAML")
        return WorkflowYaml.model_validate(content)
    except (OSError, yaml.YAMLError, ValidationError) as error:
        raise WorkflowLoadError(f"Workflow invalido en {path}: {error}") from error


def stable_id(workflow_code: str, item_code: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"sdlc-manager/{workflow_code}/{item_code}")


class WorkflowInitializer:
    def __init__(self, workflows: WorkflowRepository, projects: ProjectRepository) -> None:
        self.workflows = workflows
        self.projects = projects

    def install(self, template: WorkflowYaml) -> SdlcWorkflow:
        workflow = self.workflows.get_by_code_version(template.code, template.version)
        if workflow is None:
            workflow = SdlcWorkflow(
                id=stable_id(template.code, template.version),
                code=template.code,
                name=template.name,
                version=template.version,
                status=WorkflowStatus(template.status),
                source=template.source,
            )
            self.workflows.save_workflow(workflow)
            for stage_data in template.stages:
                stage = SdlcStage(
                    id=stable_id(template.code, stage_data.code),
                    workflow_id=workflow.id,
                    code=stage_data.code,
                    name=stage_data.name,
                    description=stage_data.description,
                    order=stage_data.order,
                    required=stage_data.required,
                )
                self.workflows.save_stage(stage)
                for gate_data in stage_data.gates:
                    self.workflows.save_gate(
                        SdlcGate(
                            id=stable_id(template.code, f"gate/{gate_data.code}"),
                            stage_id=stage.id,
                            code=gate_data.code,
                            name=gate_data.name,
                            required=gate_data.required,
                            checks=gate_data.checks,
                            conditions=gate_data.conditions,
                            enabled=gate_data.enabled,
                        )
                    )
            for exception_data in template.exceptions:
                self.workflows.save_exception(
                    SdlcException(
                        id=stable_id(template.code, f"exception/{exception_data.code}"),
                        workflow_id=workflow.id,
                        gate_code=exception_data.gate_code,
                        code=exception_data.code,
                        reason=exception_data.reason,
                        condition=exception_data.condition,
                        status=ReviewStatus.PENDING,
                        responsible=exception_data.responsible,
                        valid_from=_parse_datetime(exception_data.valid_from),
                        valid_until=_parse_datetime(exception_data.valid_until),
                        approval_source=exception_data.approval_source,
                        approval_reference=exception_data.approval_reference,
                    )
                )
        self._assign_unassigned_projects(workflow.id)
        return workflow

    def _assign_unassigned_projects(self, workflow_id: UUID) -> None:
        for project in self.projects.list_all():
            if project.workflow_id is None:
                self.projects.save(replace(project, workflow_id=workflow_id))


def _parse_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None
