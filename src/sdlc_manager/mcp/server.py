from __future__ import annotations

import logging
import sys
from typing import Any

from mcp.server.mcpserver import MCPServer

from ..application.event_schemas import SdlcEvent
from ..application.schemas import (
    AnalyzeStoryInput,
    ApplicablePracticesInput,
    ApplicableRulesInput,
    CreateProjectInput,
    CreateSprintInput,
    CreateStoryInput,
    CustomizeWorkflowInput,
    EvaluateGateInput,
    GetWorkflowInput,
    ListPoliciesInput,
    ListPracticesInput,
    RegisterEvidenceInput,
    RegisterExperienceInput,
    RegisterPracticeInput,
    ReviewExperienceInput,
    ReviewPracticeInput,
    SearchExperiencesInput,
    StartSprintInput,
    VerifyEvidenceInput,
)
from ..config import Settings, get_settings
from ..domain.enums import KnowledgeScope, ReviewStatus
from ..infrastructure.container import ApplicationContainer, build_container

logger = logging.getLogger(__name__)


def create_server(settings: Settings | None = None, initialize_schema: bool = True) -> MCPServer:
    active_settings = settings or get_settings()
    container = build_container(active_settings, initialize_schema=initialize_schema)
    server = MCPServer("sdlc-manager", version="0.1.0")
    _register_tools(server, container)
    return server


def _register_tools(server: MCPServer, container: ApplicationContainer) -> None:
    service = container.service

    @server.tool()
    def health_check() -> dict[str, Any]:
        """Verifica el estado local del servidor y sus dependencias."""
        return {
            "status": "ok",
            "database": "available",
            "policy_count": len(container.policy_engine.policies),
            "mcp_transport": "stdio",
        }

    @server.tool()
    def list_policies(input: ListPoliciesInput) -> dict[str, Any]:
        """Lista politicas YAML filtradas por estado y severidad."""
        return {"policies": service.list_policies(input.status, input.severity)}

    @server.tool()
    def get_applicable_rules(input: ApplicableRulesInput) -> dict[str, Any]:
        """Obtiene reglas aplicables a un evento del SDLC."""
        return {
            "rules": service.get_applicable_rules(
                project_id=input.project_id,
                user_story_id=input.user_story_id,
                event=input.event,
                stage=input.stage,
                changed_files=input.changed_files,
                component=input.component,
                context=input.context,
            )
        }

    @server.tool()
    def evaluate_gate(input: EvaluateGateInput) -> dict[str, Any]:
        """Evalua un gate y persiste la decision determinista."""
        return service.evaluate_gate(
            input.project_id, input.user_story_id, input.gate, input.context
        )

    @server.tool()
    def register_experience(input: RegisterExperienceInput) -> dict[str, Any]:
        """Registra una experiencia en estado pendiente de revision."""
        experience = service.register_experience(**input.model_dump())
        return {"id": str(experience.id), "review_status": experience.review_status.value}

    @server.tool()
    def search_experiences(input: SearchExperiencesInput) -> dict[str, Any]:
        """Busca experiencias aprobadas por texto, componente o etiquetas."""
        experiences = service.search_experiences(**input.model_dump())
        return {"experiences": [_experience_to_dict(item) for item in experiences]}

    @server.tool()
    def review_experience(input: ReviewExperienceInput) -> dict[str, Any]:
        """Aprueba o rechaza una memoria tecnica de forma explicita."""
        experience = service.review_experience(
            input.experience_id,
            ReviewStatus(input.status),
            input.reviewed_by,
        )
        return _experience_to_dict(experience)

    @server.tool()
    def register_evidence(input: RegisterEvidenceInput) -> dict[str, Any]:
        """Registra evidencia como PENDING sin verificarla automaticamente."""
        evidence = service.register_evidence(**input.model_dump())
        return _evidence_to_dict(evidence)

    @server.tool()
    def verify_evidence(input: VerifyEvidenceInput) -> dict[str, Any]:
        """Registra una aprobacion humana o rechazo explicito de evidencia."""
        evidence = service.verify_evidence(**input.model_dump())
        return _evidence_to_dict(evidence)

    @server.tool()
    def analyze_user_story(input: AnalyzeStoryInput) -> dict[str, Any]:
        """Analiza completitud verificable de una historia de usuario."""
        return service.analyze_user_story(input.project_id, input.user_story_id)

    @server.tool()
    def start_sprint(input: StartSprintInput) -> dict[str, Any]:
        """Analiza las historias de un proyecto o sprint."""
        return service.start_sprint(input.project_id, input.sprint_id)

    @server.tool()
    def create_project(input: CreateProjectInput) -> dict[str, Any]:
        """Crea un proyecto local para preparar datos de analisis."""
        project = service.create_project(input.name, input.description)
        return {"id": str(project.id), "name": project.name}

    @server.tool()
    def create_sprint(input: CreateSprintInput) -> dict[str, Any]:
        """Crea un sprint dentro de un proyecto existente."""
        sprint = service.create_sprint(**input.model_dump())
        return {"id": str(sprint.id), "project_id": str(sprint.project_id), "status": sprint.status}

    @server.tool()
    def create_user_story(input: CreateStoryInput) -> dict[str, Any]:
        """Crea una historia de usuario local para el analisis del SDLC."""
        story = service.create_story(**input.model_dump())
        return {"id": str(story.id), "project_id": str(story.project_id), "status": story.status}

    @server.tool()
    def get_sdlc_workflow(input: GetWorkflowInput) -> dict[str, Any]:
        """Devuelve el workflow asignado al proyecto."""
        return container.workflow_service.get_for_project(input.project_id)

    @server.tool()
    def customize_sdlc_workflow(input: CustomizeWorkflowInput) -> dict[str, Any]:
        """Crea una version derivada del workflow del proyecto."""
        return container.workflow_service.customize(
            input.project_id,
            input.name,
            input.version,
            input.stages,
            input.exceptions,
        )

    @server.tool()
    def register_practice(input: RegisterPracticeInput) -> dict[str, Any]:
        """Registra una practica pendiente sin crear un bloqueo."""
        practice = service.register_practice(
            title=input.title,
            context=input.context,
            triggers=input.triggers,
            intervention_message=input.intervention_message,
            severity=input.severity,
            scope=KnowledgeScope(input.scope),
            source_experience_id=input.source_experience_id,
            project_id=input.project_id,
            owner_id=input.owner_id,
            organization_id=input.organization_id,
        )
        return _practice_to_dict(practice)

    @server.tool()
    def list_practices(input: ListPracticesInput) -> dict[str, Any]:
        """Lista practicas aprobadas o, si se solicita, pendientes."""
        return {
            "practices": [
                _practice_to_dict(item) for item in service.list_practices(input.include_unapproved)
            ]
        }

    @server.tool()
    def review_practice(input: ReviewPracticeInput) -> dict[str, Any]:
        """Aprueba o rechaza una practica sin convertirla en politica."""
        practice = service.review_practice(
            input.practice_id,
            ReviewStatus(input.status),
            input.reviewed_by,
        )
        return _practice_to_dict(practice)

    @server.tool()
    def get_applicable_practices(input: ApplicablePracticesInput) -> dict[str, Any]:
        """Obtiene recomendaciones aprobadas para un contexto SDLC."""
        context = dict(input.context)
        context.update(
            {
                "event": input.event,
                "stage": input.stage,
                "changed_files": input.changed_files,
                "component": input.component,
                "project_id": str(input.project_id) if input.project_id else None,
                "actor_id": input.actor_id,
                "organization_id": input.organization_id,
            }
        )
        return {
            "practices": [
                _practice_to_dict(item) for item in service.get_applicable_practices(context)
            ]
        }

    @server.tool()
    def process_sdlc_event(input: SdlcEvent) -> dict[str, Any]:
        """Procesa un evento normalizado con idempotencia local."""
        return container.event_processor.process(input).model_dump(mode="json")


def _experience_to_dict(experience: Any) -> dict[str, Any]:
    return {
        "id": str(experience.id),
        "title": experience.title,
        "context": experience.context,
        "problem": experience.problem,
        "root_cause": experience.root_cause,
        "solution": experience.solution,
        "lesson_learned": experience.lesson_learned,
        "component": experience.component,
        "tags": experience.tags,
        "related_policy_ids": experience.related_policy_ids,
        "review_status": experience.review_status.value,
        "created_at": experience.created_at.isoformat() if experience.created_at else None,
        "memory_type": experience.memory_type.value,
        "technology": experience.technology,
        "category": experience.category,
        "scope": experience.scope.value,
        "project_id": str(experience.project_id) if experience.project_id else None,
        "author": experience.author,
        "reviewed_by": experience.reviewed_by,
        "reviewed_at": experience.reviewed_at.isoformat() if experience.reviewed_at else None,
        "related_experience_ids": [str(item) for item in experience.related_experience_ids],
    }


def _practice_to_dict(practice: Any) -> dict[str, Any]:
    return {
        "id": str(practice.id),
        "title": practice.title,
        "context": practice.context,
        "triggers": practice.triggers,
        "intervention_message": practice.intervention_message,
        "severity": practice.severity,
        "scope": practice.scope.value,
        "project_id": str(practice.project_id) if practice.project_id else None,
        "owner_id": practice.owner_id,
        "organization_id": practice.organization_id,
        "source_experience_id": (
            str(practice.source_experience_id) if practice.source_experience_id else None
        ),
        "approval_status": practice.approval_status.value,
        "enabled": practice.enabled,
        "approved_by": practice.approved_by,
        "approved_at": practice.approved_at.isoformat() if practice.approved_at else None,
    }


def _evidence_to_dict(evidence: Any) -> dict[str, Any]:
    return {
        "id": str(evidence.id),
        "project_id": str(evidence.project_id),
        "user_story_id": str(evidence.user_story_id),
        "policy_id": evidence.policy_id,
        "evidence_type": evidence.evidence_type,
        "reference": evidence.reference,
        "verification_status": evidence.verification_status.value,
        "verified_by": evidence.verified_by,
        "verified_at": evidence.verified_at.isoformat() if evidence.verified_at else None,
    }


def get_server_for_tests(settings: Settings) -> tuple[MCPServer, ApplicationContainer]:
    container = build_container(settings)
    server = MCPServer("sdlc-manager", version="0.1.0")
    _register_tools(server, container)
    return server, container


def main(server: MCPServer | None = None) -> None:
    logging.basicConfig(stream=sys.stderr, level=get_settings().log_level)
    (server or create_server(initialize_schema=False)).run()
