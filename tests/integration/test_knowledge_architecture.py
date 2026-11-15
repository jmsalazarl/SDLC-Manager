from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from sdlc_manager.config import Settings
from sdlc_manager.domain.enums import KnowledgeScope, MemoryType, ReviewStatus
from sdlc_manager.infrastructure.container import build_container
from sdlc_manager.infrastructure.database.db import create_database_engine
from sdlc_manager.infrastructure.database.migrations import run_migrations


def make_settings(root: Path, database_url: str) -> Settings:
    return Settings(
        database_url=database_url,
        policy_paths=[str(root / "knowledge" / "rules")],
        project_root=root,
    )


def migrate_to(settings: Settings, revision: str) -> None:
    config = Config(str(settings.project_root / "alembic.ini"))
    config.set_main_option("script_location", str(settings.project_root / "migrations"))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(config, revision)


def test_clean_install_seeds_workflow_and_keeps_memory_empty(tmp_path: Path) -> None:
    root = Path(__file__).parents[2]
    settings = make_settings(root, f"sqlite:///{tmp_path / 'clean.db'}")

    run_migrations(settings)
    container = build_container(settings, initialize_schema=False)

    engine = create_database_engine(settings.database_url)
    with engine.connect() as connection:
        assert connection.execute(sa.text("SELECT COUNT(*) FROM TPROYECTO")).scalar_one() == 0
        assert (
            connection.execute(sa.text("SELECT COUNT(*) FROM THISTORIAUSUARIO")).scalar_one() == 0
        )
        assert connection.execute(sa.text("SELECT COUNT(*) FROM TEXPERIENCIA")).scalar_one() == 0
        assert connection.execute(sa.text("SELECT COUNT(*) FROM TEVIDENCIA")).scalar_one() == 0
        assert connection.execute(sa.text("SELECT COUNT(*) FROM TEVENTOSDLC")).scalar_one() == 0
    assert container.service.search_experiences(include_unreviewed=True) == []
    project = container.service.create_project("Proyecto limpio")
    workflow = container.workflow_service.get_for_project(project.id)
    assert workflow["version"] == "1.0.0"
    assert len(workflow["stages"]) == 9
    assert container.service.projects.list_all()[0].workflow_id is not None


def test_workflow_initialization_is_idempotent(tmp_path: Path) -> None:
    root = Path(__file__).parents[2]
    settings = make_settings(root, f"sqlite:///{tmp_path / 'idempotent.db'}")

    run_migrations(settings)
    first = build_container(settings, initialize_schema=False)
    project = first.service.create_project("Proyecto persistente")
    first_workflow = first.workflow_service.get_for_project(project.id)
    second = build_container(settings, initialize_schema=False)

    assert second.workflow_service.get_for_project(project.id)["id"] == first_workflow["id"]
    assert len(second.service.projects.list_all()) == 1


def test_memory_metadata_and_practice_review_are_separated(container) -> None:
    project = container.service.create_project("Proyecto de memoria")
    experience = container.service.register_experience(
        title="Bug de consulta",
        context="Consulta de reportes",
        problem="Tiempo de respuesta alto",
        root_cause="Indice ausente",
        solution="Agregar indice",
        lesson_learned="Medir antes y despues",
        component="reporting",
        tags=["performance"],
        related_policy_ids=[],
        memory_type="BUG",
        technology="SQLite",
        category="performance",
        scope="PROJECT",
        project_id=project.id,
        author="qa-user",
        related_experience_ids=[],
    )
    assert experience.memory_type == MemoryType.BUG
    assert experience.review_status == ReviewStatus.PENDING
    assert container.service.search_experiences(include_unreviewed=False) == []

    with pytest.raises(ValueError, match="debe estar aprobada"):
        container.service.register_practice(
            title="Revisar indices",
            context="Reportes de gran volumen",
            triggers={"event": "report_change", "component": "reporting"},
            intervention_message="Revisar plan e indices",
            severity="MEDIUM",
            scope=KnowledgeScope.PROJECT,
            project_id=project.id,
            source_experience_id=experience.id,
        )

    approved = container.service.review_experience(
        experience.id, ReviewStatus.APPROVED, "tech-lead"
    )
    practice = container.service.register_practice(
        title="Revisar indices",
        context="Reportes de gran volumen",
        triggers={"event": "report_change", "components": ["reporting"]},
        intervention_message="Revisar plan e indices",
        severity="MEDIUM",
        scope=KnowledgeScope.PROJECT,
        project_id=project.id,
        source_experience_id=approved.id,
    )
    assert practice.approval_status == ReviewStatus.PENDING
    assert (
        container.service.get_applicable_practices(
            {"event": "report_change", "component": "reporting", "project_id": str(project.id)}
        )
        == []
    )
    container.service.review_practice(practice.id, ReviewStatus.APPROVED, "tech-lead")
    applicable = container.service.get_applicable_practices(
        {"event": "report_change", "component": "reporting", "project_id": str(project.id)}
    )
    assert [item.id for item in applicable] == [practice.id]
    assert all(item.approval_status == ReviewStatus.APPROVED for item in applicable)


def test_workflow_customization_is_copy_on_write(container) -> None:
    project = container.service.create_project("Proyecto configurable")
    original = container.service.projects.get(project.id)
    assert original is not None
    original_description = container.workflow_service.get_for_project(project.id)

    customized = container.workflow_service.customize(
        project.id,
        "Workflow del proyecto",
        "1.0.0-project",
        [
            {
                "code": "custom_stage",
                "name": "Etapa personalizada",
                "description": "Etapa local",
                "required": True,
                "gates": [
                    {
                        "code": "custom_gate",
                        "name": "Gate personalizado",
                        "checks": ["custom_check"],
                    }
                ],
            }
        ],
        exceptions=[
            {
                "gate_code": "custom_gate",
                "code": "approved_exception_required",
                "reason": "Excepcion temporal documentada",
                "condition": {"ticket": "required"},
            }
        ],
    )

    assert customized["version"] == "1.0.0-project"
    assert customized["stages"][0]["code"] == "custom_stage"
    assert customized["exceptions"][0]["code"] == "approved_exception_required"
    assert customized["exceptions"][0]["status"] == "PENDING"
    assert (
        container.workflow_service.get_for_project(project.id)["id"] != original_description["id"]
    )


def test_migration_from_initial_schema_preserves_experience(tmp_path: Path) -> None:
    root = Path(__file__).parents[2]
    settings = make_settings(root, f"sqlite:///{tmp_path / 'legacy.db'}")
    migrate_to(settings, "0001_initial")
    engine = create_database_engine(settings.database_url)
    with engine.begin() as connection:
        connection.execute(
            sa.text(
                "INSERT INTO TPROYECTO "
                "(CPROYECTO, NOMBRE, DESCRIPCION, FCREACION, FACTUALIZACION) "
                "VALUES (:id, :name, :description, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            ),
            {
                "id": "30e57f27-4f4c-47d0-be96-84f1b7162a99",
                "name": "Proyecto legacy",
                "description": "Datos que deben conservarse",
            },
        )
        connection.execute(
            sa.text(
                "INSERT INTO TEXPERIENCIA "
                "(CEXPERIENCIA, TITULO, CONTEXTO, PROBLEMA, CAUSARAIZ, SOLUCION, "
                "LECCIONAPRENDIDA, COMPONENTE, ETIQUETAS, REGLASRELACIONADAS, "
                "ESTADOREVISION, FCREACION) VALUES "
                "(:id, :title, :context, :problem, :root, :solution, :lesson, "
                ":component, :tags, :policies, :status, CURRENT_TIMESTAMP)"
            ),
            {
                "id": "20e57f27-4f4c-47d0-be96-84f1b7162a99",
                "title": "Experiencia legacy",
                "context": "Contexto legacy",
                "problem": "Problema legacy",
                "root": "Causa legacy",
                "solution": "Solucion legacy",
                "lesson": "Leccion legacy",
                "component": "legacy",
                "tags": "[]",
                "policies": "[]",
                "status": "PENDING",
            },
        )

    run_migrations(settings)
    container = build_container(settings, initialize_schema=False)
    memories = container.service.search_experiences(include_unreviewed=True)

    assert len(memories) == 1
    assert memories[0].id == UUID("20e57f27-4f4c-47d0-be96-84f1b7162a99")
    assert memories[0].memory_type == MemoryType.LESSON_LEARNED
    project = container.service.projects.get(UUID("30e57f27-4f4c-47d0-be96-84f1b7162a99"))
    assert project is not None
    assert project.name == "Proyecto legacy"
    assert project.workflow_id is not None


def test_workflow_enforcement_migration_is_additive(tmp_path: Path) -> None:
    root = Path(__file__).parents[2]
    settings = make_settings(root, f"sqlite:///{tmp_path / 'additive.db'}")
    migrate_to(settings, "0002_knowledge_architecture")
    engine = create_database_engine(settings.database_url)
    with engine.begin() as connection:
        connection.execute(
            sa.text(
                "INSERT INTO TPROYECTO "
                "(CPROYECTO, NOMBRE, DESCRIPCION, FCREACION, FACTUALIZACION) "
                "VALUES (:id, :name, :description, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            ),
            {
                "id": "40e57f27-4f4c-47d0-be96-84f1b7162a99",
                "name": "Proyecto previo",
                "description": "No se pierde",
            },
        )

    migrate_to(settings, "head")
    with engine.connect() as connection:
        project = connection.execute(
            sa.text("SELECT NOMBRE FROM TPROYECTO WHERE CPROYECTO = :id"),
            {"id": "40e57f27-4f4c-47d0-be96-84f1b7162a99"},
        ).scalar_one()
        practice_columns = {
            row[1] for row in connection.execute(sa.text("PRAGMA table_info(TPRACTICA)"))
        }
        exception_columns = {
            row[1] for row in connection.execute(sa.text("PRAGMA table_info(TEXCEPCIONDLC)"))
        }
        event_columns = {
            row[1] for row in connection.execute(sa.text("PRAGMA table_info(TEVENTOSDLC)"))
        }

    assert project == "Proyecto previo"
    assert {"CPROYECTO", "PROPIETARIO", "CORGANIZACION"}.issubset(practice_columns)
    assert {
        "RESPONSABLE",
        "FINICIO",
        "FFIN",
        "FUENTEAPROBACION",
        "REFERENCIAAPROBACION",
    }.issubset(exception_columns)
    assert {"CEVENTO", "HUELLA", "ESTADO", "RESULTADO", "FCREACION"}.issubset(event_columns)
