from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from ...domain.enums import ReviewStatus, WorkflowStatus
from ...domain.models import SdlcException, SdlcGate, SdlcStage, SdlcWorkflow
from ...domain.ports.repositories import ProjectRepository, WorkflowRepository


class WorkflowService:
    def __init__(self, workflows: WorkflowRepository, projects: ProjectRepository) -> None:
        self.workflows = workflows
        self.projects = projects

    def get_for_project(self, project_id: UUID) -> dict[str, object]:
        project = self.projects.get(project_id)
        if project is None:
            raise ValueError("Proyecto no encontrado")
        workflow = self.workflows.get(project.workflow_id) if project.workflow_id else None
        if workflow is None:
            raise ValueError("El proyecto no tiene workflow asignado")
        return self.describe(workflow.id)

    def describe(self, workflow_id: UUID) -> dict[str, object]:
        workflow = self.workflows.get(workflow_id)
        if workflow is None:
            raise ValueError("Workflow no encontrado")
        stages = self.workflows.list_stages(workflow.id)
        gates = self.workflows.list_gates(workflow.id)
        exceptions = self.workflows.list_exceptions(workflow.id)
        gates_by_stage: dict[UUID, list[SdlcGate]] = {}
        for gate in gates:
            gates_by_stage.setdefault(gate.stage_id, []).append(gate)
        return {
            "id": str(workflow.id),
            "code": workflow.code,
            "name": workflow.name,
            "version": workflow.version,
            "status": workflow.status.value,
            "source": workflow.source,
            "stages": [
                {
                    "id": str(stage.id),
                    "code": stage.code,
                    "name": stage.name,
                    "description": stage.description,
                    "order": stage.order,
                    "required": stage.required,
                    "gates": [
                        {
                            "id": str(gate.id),
                            "code": gate.code,
                            "name": gate.name,
                            "required": gate.required,
                            "checks": gate.checks,
                            "conditions": gate.conditions,
                            "enabled": gate.enabled,
                        }
                        for gate in gates_by_stage.get(stage.id, [])
                    ],
                }
                for stage in stages
            ],
            "exceptions": [
                {
                    "id": str(item.id),
                    "gate_code": item.gate_code,
                    "code": item.code,
                    "reason": item.reason,
                    "condition": item.condition,
                    "status": item.status.value,
                    "approved_by": item.approved_by,
                    "approved_at": item.approved_at.isoformat() if item.approved_at else None,
                    "responsible": item.responsible,
                    "valid_from": item.valid_from.isoformat() if item.valid_from else None,
                    "valid_until": item.valid_until.isoformat() if item.valid_until else None,
                    "approval_source": item.approval_source,
                    "approval_reference": item.approval_reference,
                }
                for item in exceptions
            ],
        }

    def customize(
        self,
        project_id: UUID,
        name: str,
        version: str,
        stages: list[dict[str, Any]],
        exceptions: list[dict[str, Any]] | None = None,
    ) -> dict[str, object]:
        project = self.projects.get(project_id)
        if project is None:
            raise ValueError("Proyecto no encontrado")
        if project.workflow_id is None:
            raise ValueError("El proyecto no tiene workflow asignado")
        source = self.workflows.get(project.workflow_id)
        if source is None:
            raise ValueError("Workflow de origen no encontrado")
        workflow = self.workflows.save_workflow(
            SdlcWorkflow(
                id=uuid4(),
                code=f"{source.code}-{project_id.hex[:8]}",
                name=name,
                version=version,
                status=WorkflowStatus.DRAFT,
                source=f"derived:{source.id}",
            )
        )
        for position, data in enumerate(stages, start=1):
            stage = self.workflows.save_stage(
                SdlcStage(
                    id=uuid4(),
                    workflow_id=workflow.id,
                    code=str(data["code"]),
                    name=str(data["name"]),
                    description=str(data.get("description", "")),
                    order=int(data.get("order", position)),
                    required=bool(data.get("required", True)),
                )
            )
            for gate_data in data.get("gates", []):
                if not isinstance(gate_data, dict):
                    raise ValueError("Cada gate personalizado debe ser un objeto")
                self.workflows.save_gate(
                    SdlcGate(
                        id=uuid4(),
                        stage_id=stage.id,
                        code=str(gate_data["code"]),
                        name=str(gate_data["name"]),
                        required=bool(gate_data.get("required", True)),
                        checks=[str(item) for item in gate_data.get("checks", [])],
                        conditions=gate_data.get("conditions", {}),
                        enabled=bool(gate_data.get("enabled", True)),
                    )
                )
        for exception_data in exceptions or []:
            if not isinstance(exception_data, dict):
                raise ValueError("Cada excepcion personalizada debe ser un objeto")
            valid_from = self._parse_datetime(exception_data.get("valid_from"))
            valid_until = self._parse_datetime(exception_data.get("valid_until"))
            self.workflows.save_exception(
                SdlcException(
                    id=uuid4(),
                    workflow_id=workflow.id,
                    gate_code=str(exception_data["gate_code"]),
                    code=str(exception_data["code"]),
                    reason=str(exception_data["reason"]),
                    condition=exception_data.get("condition", {}),
                    status=ReviewStatus.PENDING,
                    responsible=exception_data.get("responsible"),
                    valid_from=valid_from,
                    valid_until=valid_until,
                    approval_source=exception_data.get("approval_source"),
                    approval_reference=exception_data.get("approval_reference"),
                )
            )
        self.projects.save(replace(project, workflow_id=workflow.id))
        return self.describe(workflow.id)

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("La vigencia de una excepcion debe ser una fecha ISO")
        try:
            return datetime.fromisoformat(value)
        except ValueError as error:
            raise ValueError("La vigencia de una excepcion debe ser una fecha ISO") from error
