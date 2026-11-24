from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path
from uuid import UUID

import pytest
from integrations.common.event_adapter import normalize_file_event, stable_event_id

from sdlc_manager.config import Settings
from sdlc_manager.domain.enums import KnowledgeScope, ReviewStatus
from sdlc_manager.infrastructure.container import build_container
from sdlc_manager.infrastructure.database.migrations import run_migrations

ROOT = Path(__file__).parents[2]


def test_client_mcp_configurations_are_present_and_structured() -> None:
    kiro = json.loads((ROOT / "integrations/kiro/mcp.native.example.json").read_text())
    claude = json.loads((ROOT / "integrations/claude-code/.mcp.json.example").read_text())
    opencode = json.loads(
        (ROOT / "integrations/opencode/opencode.config.example.jsonc").read_text()
    )
    codex = tomllib.loads((ROOT / "integrations/codex/mcp.config.example.toml").read_text())

    assert "mcpServers" in kiro
    assert "sdlc-manager" in kiro["mcpServers"]
    assert claude["mcpServers"]["sdlc-manager"]["type"] == "stdio"
    assert opencode["mcp"]["servers"]["sdlc-manager"]["type"] == "local"
    assert codex["mcp_servers"]["sdlc-manager"]["command"] == "uv"


def test_kiro_hook_is_disabled_and_non_blocking_by_default() -> None:
    hook = json.loads((ROOT / "integrations/kiro/hooks/sdlc-file-save.example.json").read_text())
    installed = json.loads(
        (ROOT / "integrations/kiro/hooks/sdlc-file-save.installed.json").read_text()
    )

    assert hook["version"] == "v1"
    assert hook["hooks"][0]["trigger"] == "PostFileSave"
    assert hook["hooks"][0]["enabled"] is False
    assert installed["hooks"][0]["enabled"] is True
    assert "html" in installed["hooks"][0]["matcher"]
    assert "hook kiro" in installed["hooks"][0]["action"]["command"]
    assert "__SDLC_MANAGER_COMMAND__" in installed["hooks"][0]["action"]["command"]


def test_normalized_event_preserves_stable_event_id() -> None:
    native = {"path": "artifacts/sample.artifact", "session_id": "session-1"}
    first = normalize_file_event(native, "kiro", "00e57f27-4f4c-47d0-be96-84f1b7162a99")
    second = normalize_file_event(native, "kiro", "00e57f27-4f4c-47d0-be96-84f1b7162a99")

    assert first == second
    assert UUID(first["event_id"])
    assert first["event_type"] == "file_changed"
    assert first["source_client"] == "kiro"


def test_normalized_event_rejects_invalid_project_and_path() -> None:
    with pytest.raises(ValueError, match="UUID"):
        normalize_file_event({"path": "file.py"}, "kiro", "invalid")
    with pytest.raises(ValueError, match="segura"):
        normalize_file_event(
            {"path": "../secret.py"},
            "kiro",
            "00e57f27-4f4c-47d0-be96-84f1b7162a99",
        )


def test_stable_event_id_uses_valid_native_uuid() -> None:
    event_id = "00e57f27-4f4c-47d0-be96-84f1b7162a99"

    assert stable_event_id("codex", "file_changed", "identity", event_id) == event_id


def test_kiro_adapter_translates_payload_and_exposes_context(tmp_path: Path) -> None:
    fake_cli = tmp_path / "fake_cli.py"
    fake_cli.write_text(
        "import json, sys\n"
        "payload = json.load(sys.stdin)\n"
        "print(json.dumps({'source_client': payload['source_client'], "
        "'event_type': payload['event_type'], 'recommendations': "
        "['Revisar el componente relacionado'], 'decision': 'WARN'}))\n"
    )
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONPATH": str(ROOT),
            "SDLC_MANAGER_PROJECT_ID": "00e57f27-4f4c-47d0-be96-84f1b7162a99",
            "SDLC_MANAGER_COMMAND": f"{sys.executable} {fake_cli}",
        }
    )
    process = subprocess.run(
        [sys.executable, str(ROOT / "integrations/kiro/kiro_event_adapter.py")],
        input=json.dumps(
            {
                "path": "artifacts/sample.artifact",
                "session_id": "s-1",
            }
        ).encode(),
        capture_output=True,
        cwd=ROOT,
        env=environment,
        check=False,
    )

    assert process.returncode == 0
    assert process.stdout.decode().startswith("SDLC Manager:\n- Revisar el componente relacionado")
    assert "Decision: WARN." in process.stdout.decode()
    assert process.stderr == b""


def test_kiro_adapter_rejects_payload_without_file(tmp_path: Path) -> None:
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONPATH": str(ROOT),
            "SDLC_MANAGER_PROJECT_ID": "00e57f27-4f4c-47d0-be96-84f1b7162a99",
        }
    )
    process = subprocess.run(
        [sys.executable, str(ROOT / "integrations/kiro/kiro_event_adapter.py")],
        input=json.dumps({"session_id": "s-1"}).encode(),
        capture_output=True,
        cwd=ROOT,
        env=environment,
        check=False,
    )

    assert process.returncode == 40
    assert json.loads(process.stdout)["error_code"] == "INVALID_EVENT"


def test_kiro_adapter_processes_real_post_file_save_payload_from_external_workspace(
    tmp_path: Path,
) -> None:
    database = tmp_path / "sdlc-manager.db"
    settings = Settings(
        database_url=f"sqlite:///{database}",
        policy_paths=[str(ROOT / "knowledge" / "rules")],
        project_root=ROOT,
    )
    run_migrations(settings)
    container = build_container(settings, initialize_schema=False)
    project = container.service.create_project("Kiro external workspace")
    practice = container.service.register_practice(
        title="Kiro payment practice",
        context="Payment changes require review",
        triggers={"event": "file_change", "components": ["payments"]},
        intervention_message="Review the payment change",
        severity="LOW",
        scope=KnowledgeScope.PROJECT,
        project_id=project.id,
    )
    container.service.review_practice(practice.id, ReviewStatus.APPROVED, "reviewer")

    source_file = tmp_path / "src" / "payments" / "payment_service.py"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("class PaymentService:\n    pass\n", encoding="utf-8")
    config_dir = tmp_path / ".sdlc-manager"
    config_dir.mkdir()
    (config_dir / "config.json").write_text(
        json.dumps({"project_id": str(project.id)}), encoding="utf-8"
    )
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONPATH": str(ROOT),
            "SDLC_MANAGER_DATABASE_URL": f"sqlite:///{database}",
            "SDLC_MANAGER_PROJECT_ROOT": str(tmp_path),
            "SDLC_MANAGER_AUTO_MIGRATE": "true",
        }
    )
    process = subprocess.run(
        [sys.executable, str(ROOT / "integrations/kiro/kiro_event_adapter.py")],
        input=json.dumps(
            {
                "session_id": "kiro-real-post-file-save",
                "hook_event_name": "PostFileSave",
                "cwd": str(tmp_path),
                "file_path": str(source_file),
                "timestamp": "2026-11-22T00:00:00Z",
            }
        ).encode(),
        capture_output=True,
        cwd=tmp_path,
        env=environment,
        check=False,
    )

    assert process.returncode == 0
    assert process.stdout.decode().startswith(
        "SDLC Manager:\n- Practica: Review the payment change"
    )


def test_manual_client_wrappers_override_transport_source(tmp_path: Path) -> None:
    fake_cli = tmp_path / "fake_cli.py"
    fake_cli.write_text(
        "import json, sys\n"
        "payload = json.load(sys.stdin)\n"
        "print(json.dumps({'source_client': payload['source_client']}))\n"
    )
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONPATH": str(ROOT),
            "SDLC_MANAGER_COMMAND": f"{sys.executable} {fake_cli}",
        }
    )
    event = {
        "event_id": "00e57f27-4f4c-47d0-be96-84f1b7162a99",
        "event_type": "session_started",
        "source_client": "untrusted",
        "timestamp": "2026-11-15T00:00:00Z",
        "context": {},
    }
    process = subprocess.run(
        [sys.executable, str(ROOT / "integrations/claude-code/process_event.py")],
        input=json.dumps(event).encode(),
        capture_output=True,
        cwd=ROOT,
        env=environment,
        check=False,
    )

    assert process.returncode == 0
    assert json.loads(process.stdout)["source_client"] == "claude-code"
    assert process.stderr == b""


def test_opencode_adapter_normalizes_native_file_event(tmp_path: Path) -> None:
    fake_cli = tmp_path / "fake_cli.py"
    fake_cli.write_text(
        "import json, sys\n"
        "payload = json.load(sys.stdin)\n"
        "print(json.dumps({'event_type': payload['event_type'], "
        "'source_client': payload['source_client'], 'affected_files': "
        "payload['affected_files']}))\n"
    )
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONPATH": str(ROOT),
            "SDLC_MANAGER_PROJECT_ID": "00e57f27-4f4c-47d0-be96-84f1b7162a99",
            "SDLC_MANAGER_COMMAND": f"{sys.executable} {fake_cli}",
        }
    )
    process = subprocess.run(
        [sys.executable, str(ROOT / "integrations/opencode/process_event.py")],
        input=json.dumps(
            {
                "event_type": "file_changed",
                "project_root": str(tmp_path),
                "path": "src/payments.py",
                "timestamp": "2026-11-19T00:00:00Z",
            }
        ).encode(),
        capture_output=True,
        cwd=tmp_path,
        env=environment,
        check=False,
    )

    assert process.returncode == 0
    assert json.loads(process.stdout) == {
        "event_type": "file_changed",
        "source_client": "opencode",
        "affected_files": ["src/payments.py"],
    }
    assert process.stderr == b""
