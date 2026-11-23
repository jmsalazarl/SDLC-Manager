from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from sdlc_manager.config import Settings
from sdlc_manager.domain.enums import KnowledgeScope, ReviewStatus
from sdlc_manager.infrastructure.container import build_container
from sdlc_manager.infrastructure.database.migrations import run_migrations

ROOT = Path(__file__).parents[2]


def cli_env(database: Path) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONPATH": str(ROOT / "src"),
            "SDLC_MANAGER_DATABASE_URL": f"sqlite:///{database}",
            "SDLC_MANAGER_POLICY_PATHS": json.dumps([str(ROOT / "knowledge" / "rules")]),
            "SDLC_MANAGER_PROJECT_ROOT": str(ROOT),
            "SDLC_MANAGER_AUTO_MIGRATE": "true",
        }
    )
    return environment


def invoke_cli(database: Path, payload: object, *, environment: dict[str, str] | None = None):
    env = cli_env(database)
    if environment:
        env.update(environment)
    return subprocess.run(
        [sys.executable, "-m", "sdlc_manager", "event", "process", "--stdin"],
        input=json.dumps(payload).encode("utf-8") if not isinstance(payload, bytes) else payload,
        capture_output=True,
        cwd=ROOT,
        env=env,
        check=False,
    )


def prepare_project(database: Path) -> tuple[UUID, UUID, UUID]:
    settings = Settings(
        database_url=f"sqlite:///{database}",
        policy_paths=[str(ROOT / "knowledge" / "rules")],
        project_root=ROOT,
    )
    run_migrations(settings)
    container = build_container(settings, initialize_schema=False)
    project = container.service.create_project("CLI project")
    ready_story = container.service.create_story(
        project.id,
        "Ready story",
        description="Implement the change",
        acceptance_criteria=["The change is verifiable"],
    )
    blocked_story = container.service.create_story(project.id, "Incomplete story")
    practice = container.service.register_practice(
        title="CLI practice",
        context="CLI context",
        triggers={"event": "file_change", "components": ["payments"]},
        intervention_message="Review the payment change",
        severity="LOW",
        scope=KnowledgeScope.PROJECT,
        project_id=project.id,
    )
    container.service.review_practice(practice.id, ReviewStatus.APPROVED, "reviewer")
    return project.id, ready_story.id, blocked_story.id


def event_payload(
    event_type: str,
    *,
    project_id: UUID | None = None,
    user_story_id: UUID | None = None,
    event_id: UUID | None = None,
    context: dict[str, object] | None = None,
    affected_files: list[str] | None = None,
) -> dict[str, object]:
    return {
        "event_id": str(event_id or uuid4()),
        "event_type": event_type,
        "source_client": "cli-test",
        "project_id": str(project_id) if project_id else None,
        "user_story_id": str(user_story_id) if user_story_id else None,
        "timestamp": "2026-11-15T00:00:00Z",
        "affected_files": affected_files or [],
        "context": context or {},
    }


def result(process: subprocess.CompletedProcess[bytes]) -> dict[str, object]:
    assert process.stdout.endswith(b"\n")
    return json.loads(process.stdout)


def test_cli_returns_distinct_info_pass_warn_and_block_codes(tmp_path: Path) -> None:
    database = tmp_path / "cli.db"
    project_id, ready_story_id, blocked_story_id = prepare_project(database)

    info = invoke_cli(database, event_payload("session_started"))
    passed = invoke_cli(
        database,
        event_payload("user_story_started", project_id=project_id, user_story_id=ready_story_id),
    )
    warned = invoke_cli(
        database,
        event_payload("file_changed", project_id=project_id, context={"component": "payments"}),
    )
    blocked = invoke_cli(
        database,
        event_payload("user_story_started", project_id=project_id, user_story_id=blocked_story_id),
    )

    assert info.returncode == 0
    assert result(info)["decision"] is None
    assert passed.returncode == 10
    assert result(passed)["decision"] == "PASS"
    assert warned.returncode == 20
    assert result(warned)["decision"] == "WARN"
    assert blocked.returncode == 30
    assert result(blocked)["decision"] == "BLOCK"


def test_cli_rejects_invalid_json_uuid_and_oversized_input(tmp_path: Path) -> None:
    database = tmp_path / "invalid.db"
    invalid_json = invoke_cli(database, b"{not-json")
    invalid_uuid = invoke_cli(
        database,
        {
            "event_id": "not-a-uuid",
            "event_type": "session_started",
            "source_client": "cli-test",
            "timestamp": "2026-11-15T00:00:00Z",
            "context": {},
        },
    )
    oversized = invoke_cli(database, b"{" + b"a" * (1024 * 1024) + b"}")

    assert invalid_json.returncode == 40
    assert result(invalid_json)["error_code"] == "INVALID_JSON"
    assert invalid_uuid.returncode == 40
    assert result(invalid_uuid)["error_code"] == "INVALID_EVENT"
    assert oversized.returncode == 40
    assert result(oversized)["error_code"] == "INPUT_TOO_LARGE"


def test_cli_persists_duplicate_and_rejects_conflicting_event(tmp_path: Path) -> None:
    database = tmp_path / "idempotence.db"
    event_id = uuid4()
    first_payload = event_payload("session_started", event_id=event_id)
    conflict_payload = event_payload(
        "session_started", event_id=event_id, context={"different": True}
    )

    first = invoke_cli(database, first_payload)
    duplicate = invoke_cli(database, first_payload)
    conflict = invoke_cli(database, conflict_payload)

    assert first.returncode == 0
    assert result(first)["status"] == "PROCESSED"
    assert duplicate.returncode == 0
    assert result(duplicate)["status"] == "DUPLICATE"
    assert conflict.returncode == 40
    assert result(conflict)["error_code"] == "EVENT_ID_REUSED"


def test_cli_reports_bootstrap_error_without_success(tmp_path: Path) -> None:
    process = invoke_cli(
        tmp_path / "unused.db",
        event_payload("session_started"),
        environment={"SDLC_MANAGER_DATABASE_URL": "sqlite:////proc/sdlc-manager.db"},
    )

    assert process.returncode == 50
    assert result(process)["status"] == "ERROR"
    assert result(process)["error_code"] == "CLI_BOOTSTRAP_ERROR"
    assert process.stderr


def test_cli_uses_installed_resources_from_external_project_root(tmp_path: Path) -> None:
    database = tmp_path / "external.db"
    environment = cli_env(database)
    environment.update(
        {
            "SDLC_MANAGER_PROJECT_ROOT": str(tmp_path),
            "SDLC_MANAGER_POLICY_PATHS": json.dumps(["knowledge/rules"]),
            "SDLC_MANAGER_WORKFLOW_TEMPLATE_PATH": "knowledge/sdlc/default.yaml",
        }
    )

    process = invoke_cli(database, event_payload("session_started"), environment=environment)

    assert process.returncode == 0
    assert result(process)["status"] == "PROCESSED"


@pytest.mark.skipif(
    os.getenv("SDLC_MANAGER_RUN_DOCKER_TESTS") != "1" or shutil.which("docker") is None,
    reason="La prueba Docker se habilita explicitamente con SDLC_MANAGER_RUN_DOCKER_TESTS=1",
)
def test_cli_runs_in_docker_with_persistent_volume() -> None:
    volume = f"sdlc-manager-cli-test-{uuid4().hex}"
    event = event_payload("session_started", event_id=uuid4())
    try:
        created = subprocess.run(["docker", "volume", "create", volume], check=False)
        assert created.returncode == 0
        command = [
            "docker",
            "run",
            "--rm",
            "-i",
            "--network",
            "none",
            "-v",
            f"{volume}:/app/data",
            "sdlc-manager:latest",
            "event",
            "process",
            "--stdin",
        ]
        first = subprocess.run(
            command,
            input=json.dumps(event).encode("utf-8"),
            capture_output=True,
            check=False,
        )
        second = subprocess.run(
            command,
            input=json.dumps(event).encode("utf-8"),
            capture_output=True,
            check=False,
        )
        assert first.returncode == 0
        assert second.returncode == 0
        assert json.loads(first.stdout)["status"] == "PROCESSED"
        assert json.loads(second.stdout)["status"] == "DUPLICATE"
    finally:
        subprocess.run(["docker", "volume", "rm", "-f", volume], check=False)
