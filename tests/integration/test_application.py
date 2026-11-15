from __future__ import annotations

from sdlc_manager.domain.enums import EvaluationResult, EvidenceStatus


def test_evaluate_gate_and_evidence_lifecycle(container) -> None:
    service = container.service
    project = service.create_project("Demo")
    story = service.create_story(project.id, "Actualizar formulario", "Descripcion", ["WHEN ok"])

    blocked = service.evaluate_gate(
        project.id,
        story.id,
        "task_completion",
        {"event": "file_change", "changed_files": ["forms/customer.wpx"]},
    )
    assert blocked["result"] == EvaluationResult.BLOCK
    assert set(blocked["missing_evidence"]) == {
        "production_version",
        "comparison_result",
        "compatibility_validation",
        "closure_evidence",
    }

    for evidence_type in blocked["missing_evidence"]:
        evidence = service.register_evidence(
            project.id,
            story.id,
            "SDLC-001" if evidence_type != "closure_evidence" else "WORKFLOW",
            evidence_type,
            f"record:{evidence_type}",
        )
        assert evidence.verification_status == EvidenceStatus.PENDING
        service.verify_evidence(project.id, evidence.id, "human-reviewer")

    passed = service.evaluate_gate(
        project.id,
        story.id,
        "task_completion",
        {"event": "file_change", "changed_files": ["forms/customer.wpx"]},
    )
    assert passed["result"] == EvaluationResult.PASS


def test_experience_search_hides_unreviewed_by_default(container) -> None:
    service = container.service
    service.register_experience(
        title="Incidente de cache",
        context="Servicio local",
        problem="Datos obsoletos",
        root_cause="Invalidacion tardia",
        solution="Se agrego una invalidacion explicita",
        lesson_learned="Verificar cache en el gate",
        component="catalog",
        tags=["cache", "incident"],
        related_policy_ids=[],
    )
    assert service.search_experiences(query="cache") == []
    assert len(service.search_experiences(query="cache", include_unreviewed=True)) == 1


def test_project_isolation_and_user_story_analysis(container) -> None:
    service = container.service
    first = service.create_project("First")
    second = service.create_project("Second")
    story = service.create_story(first.id, "Incomplete", description=None)

    analysis = service.analyze_user_story(first.id, story.id)
    assert analysis["ready_for_development"] is False
    assert "missing_description" in analysis["issues"]
    assert "missing_acceptance_criteria" in analysis["issues"]
    assert service.start_sprint(second.id)["total_stories"] == 0
