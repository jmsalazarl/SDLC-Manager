from __future__ import annotations

from datetime import UTC, datetime, timedelta

import sqlalchemy as sa

from sdlc_manager.domain.enums import EvaluationResult, KnowledgeScope, ReviewStatus


def test_default_workflow_blocks_incomplete_story_and_design_gate_is_conditional(container) -> None:
    service = container.service
    project = service.create_project("Workflow project")
    story = service.create_story(project.id, "Historia incompleta", description=None)

    acceptance = service.evaluate_gate(project.id, story.id, "acceptance_ready")
    development = service.evaluate_gate(
        project.id,
        story.id,
        "development_start",
        {"event": "development_start"},
    )
    design_not_required = service.evaluate_gate(project.id, story.id, "design_approved")
    design_required = service.evaluate_gate(
        project.id,
        story.id,
        "design_approved",
        {"design_required": True},
    )

    assert acceptance["result"] == EvaluationResult.BLOCK
    assert development["result"] == EvaluationResult.BLOCK
    assert "SDLC-003" in development["deduplicated_policy_rules"]
    assert design_not_required["result"] == EvaluationResult.PASS
    assert design_not_required["not_applicable_checks"] == ["design_evidence"]
    assert design_required["result"] == EvaluationResult.BLOCK


def test_all_default_workflow_gates_are_executable(container) -> None:
    service = container.service
    project = service.create_project("All gates project")
    story = service.create_story(
        project.id,
        "Historia completa",
        description="Descripcion",
        acceptance_criteria=["Criterio"],
        dependencies=[{"status": "RESOLVED"}],
    )
    gates = [
        "refinement_complete",
        "acceptance_ready",
        "dependencies_ready",
        "design_approved",
        "development_start",
        "technical_review",
        "testing_complete",
        "deployment_ready",
        "task_completion",
    ]

    decisions = [service.evaluate_gate(project.id, story.id, gate) for gate in gates]

    assert [decision["gate"] for decision in decisions] == gates
    assert all(decision["result"] in {"PASS", "WARN", "BLOCK"} for decision in decisions)


def test_testing_and_closure_require_verified_workflow_evidence(container) -> None:
    service = container.service
    project = service.create_project("Evidence project")
    story = service.create_story(
        project.id,
        "Historia lista",
        description="Descripcion",
        acceptance_criteria=["Criterio"],
        dependencies=[{"status": "RESOLVED"}],
    )

    testing = service.evaluate_gate(project.id, story.id, "testing_complete")
    pending = service.register_evidence(
        project.id, story.id, "WORKFLOW", "test_evidence", "record:test"
    )
    pending_result = service.evaluate_gate(project.id, story.id, "testing_complete")
    service.verify_evidence(project.id, pending.id, "human-reviewer")
    passed = service.evaluate_gate(project.id, story.id, "testing_complete")
    closure = service.evaluate_gate(project.id, story.id, "task_completion")

    assert testing["result"] == EvaluationResult.BLOCK
    assert pending_result["pending_evidence"] == ["test_evidence"]
    assert passed["result"] == EvaluationResult.PASS
    assert closure["result"] == EvaluationResult.BLOCK


def test_gate_customization_and_untrusted_exception_keep_enforcement(container) -> None:
    service = container.service
    project = service.create_project("Exception project")
    story = service.create_story(project.id, "Historia", description="Descripcion")
    workflow = container.workflow_service.customize(
        project.id,
        "Workflow personalizado",
        "1.0.0-custom",
        [
            {
                "code": "custom_stage",
                "name": "Etapa personalizada",
                "description": "Etapa",
                "gates": [
                    {
                        "code": "custom_gate",
                        "name": "Gate",
                        "required": True,
                        "checks": ["closure_evidence"],
                    }
                ],
            }
        ],
        exceptions=[
            {
                "gate_code": "custom_gate",
                "code": "temporary_exception",
                "reason": "Motivo",
                "condition": {},
                "responsible": "reviewer",
                "valid_from": (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
                "valid_until": (datetime.now(UTC) + timedelta(minutes=1)).isoformat(),
                "approval_reference": "ticket:123",
            }
        ],
    )
    assert workflow["exceptions"][0]["status"] == ReviewStatus.PENDING
    blocked = service.evaluate_gate(project.id, story.id, "custom_gate")
    assert blocked["result"] == EvaluationResult.BLOCK


def test_gate_and_evidence_decisions_are_audited(container) -> None:
    service = container.service
    project = service.create_project("Audit project")
    story = service.create_story(project.id, "Historia", description="Descripcion")
    service.evaluate_gate(project.id, story.id, "testing_complete")
    evidence = service.register_evidence(
        project.id, story.id, "WORKFLOW", "test_evidence", "record:test"
    )
    service.verify_evidence(project.id, evidence.id, "human-reviewer", approved=False)

    engine = container.service.projects.factory.kw["bind"]
    with engine.connect() as connection:
        events = (
            connection.execute(
                sa.text("SELECT TIPOEVENTO FROM TAUDITORIA WHERE CPROYECTO = :project"),
                {"project": str(project.id)},
            )
            .scalars()
            .all()
        )
    assert "gate_evaluated" in events
    assert "gate_blocked" in events
    assert "evidence_registered" in events
    assert "evidence_status_changed" in events


def test_project_and_personal_practices_are_isolated(container) -> None:
    service = container.service
    first = service.create_project("First practice project")
    second = service.create_project("Second practice project")
    project_practice = service.register_practice(
        title="Project recommendation",
        context="Project context",
        triggers={"event": "file_change"},
        intervention_message="Review project context",
        severity="MEDIUM",
        scope=KnowledgeScope.PROJECT,
        project_id=first.id,
    )
    personal_practice = service.register_practice(
        title="Personal recommendation",
        context="Personal context",
        triggers={"event": "file_change"},
        intervention_message="Review personal context",
        severity="LOW",
        scope=KnowledgeScope.PERSONAL,
        owner_id="user-a",
    )
    service.review_practice(project_practice.id, ReviewStatus.APPROVED, "reviewer")
    service.review_practice(personal_practice.id, ReviewStatus.APPROVED, "reviewer")

    first_results = service.get_applicable_practices(
        {"event": "file_change", "project_id": str(first.id), "actor_id": "user-a"}
    )
    second_results = service.get_applicable_practices(
        {"event": "file_change", "project_id": str(second.id), "actor_id": "user-b"}
    )

    assert {item.id for item in first_results} == {project_practice.id, personal_practice.id}
    assert second_results == []
