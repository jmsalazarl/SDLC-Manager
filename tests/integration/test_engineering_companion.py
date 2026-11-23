from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest
from integrations.common.event_adapter import project_id_from_environment
from integrations.common.hook_runner import normalize_native_event

from sdlc_manager.domain.enums import ReviewStatus
from sdlc_manager.infrastructure.integrations.installer import (
    IntegrationError,
    IntegrationInstaller,
)
from sdlc_manager.infrastructure.sddnxp.reader import SddnxpReader

ROOT = Path(__file__).parents[2]
PROJECT_ID = "00e57f27-4f4c-47d0-be96-84f1b7162a99"


def test_file_event_recovers_experience_from_inferred_component(container) -> None:
    project = container.service.create_project("Payments companion project")
    experience = container.service.register_experience(
        title="Desactivacion segura de funcionalidad critica",
        context="Cambios en pagos",
        problem="Una activacion parcial genero regresion",
        root_cause="No existia una salida controlada",
        solution="Usar feature flag con rollback probado",
        lesson_learned="Validar el apagado antes del despliegue",
        component="payments",
        tags=["feature-flag", "regresion"],
        related_policy_ids=[],
        scope="PROJECT",
        project_id=project.id,
        author="reviewer",
    )
    container.service.review_experience(experience.id, ReviewStatus.APPROVED, "reviewer")

    result = container.event_processor.process_payload(
        {
            "event_id": "11111111-1111-4111-8111-111111111111",
            "event_type": "file_changed",
            "source_client": "test-client",
            "project_id": str(project.id),
            "timestamp": "2026-11-15T00:00:00Z",
            "affected_files": ["src/payments/PaymentService.py"],
            "context": {},
        }
    )

    assert result.relevant_experiences == [str(experience.id)]


def test_sddnxp_reader_is_optional_and_read_only(tmp_path: Path) -> None:
    spec_dir = tmp_path / ".sdd" / "specs" / "demo"
    spec_dir.mkdir(parents=True)
    (tmp_path / ".sdd" / "config.yaml").write_text(
        "schemaVersion: '1.0'\nprojectId: demo\nprojectName: Demo\n", encoding="utf-8"
    )
    (spec_dir / "spec.yaml").write_text(
        "specId: SPEC-001\nname: demo\nversion: '1.0.0'\nstatus: implemented\n",
        encoding="utf-8",
    )

    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    result = SddnxpReader(tmp_path).read()
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    assert result is not None
    assert result["status"] == "available"
    assert result["spec_count"] == 1
    assert before == after
    assert SddnxpReader(tmp_path / "without-sddnxp").read() is None


def test_hook_runner_relativizes_absolute_provider_paths(tmp_path: Path) -> None:
    event = normalize_native_event(
        {
            "hook_event_name": "PostToolUse",
            "cwd": str(tmp_path),
            "project_id": PROJECT_ID,
            "tool_input": {"file_path": str(tmp_path / "src" / "payments.py")},
        },
        "claude-code",
    )

    assert event["affected_files"] == ["src/payments.py"]

    with pytest.raises(ValueError, match="fuera del proyecto"):
        normalize_native_event(
            {
                "hook_event_name": "PostToolUse",
                "cwd": str(tmp_path),
                "project_id": PROJECT_ID,
                "tool_input": {"file_path": str(tmp_path.parent / "outside.py")},
            },
            "claude-code",
        )


def test_codex_apply_patch_payload_extracts_changed_file(tmp_path: Path) -> None:
    event = normalize_native_event(
        {
            "hook_event_name": "PostToolUse",
            "cwd": str(tmp_path),
            "project_id": PROJECT_ID,
            "tool_name": "apply_patch",
            "tool_input": {
                "command": (
                    "*** Begin Patch\n"
                    "*** Update File: src/payments/payment_service.py\n"
                    "@@\n"
                    "*** End Patch"
                )
            },
        },
        "codex",
    )

    assert event["affected_files"] == ["src/payments/payment_service.py"]


def test_project_id_can_be_loaded_from_managed_project_config(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / ".sdlc-manager" / "config.json"
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps({"project_id": PROJECT_ID}), encoding="utf-8")
    monkeypatch.delenv("SDLC_MANAGER_PROJECT_ID", raising=False)
    monkeypatch.chdir(tmp_path)

    assert project_id_from_environment() == PROJECT_ID


def test_hook_output_is_visible_and_keeps_json_stdout(tmp_path: Path) -> None:
    fake_cli = tmp_path / "fake_cli.py"
    fake_cli.write_text(
        "import json, sys\n"
        "payload = json.load(sys.stdin)\n"
        "print(json.dumps({'event_type': payload['event_type'], "
        "'source_client': payload['source_client']}))\n"
        "print('diagnostic', file=sys.stderr)\n"
        "raise SystemExit(20)\n",
        encoding="utf-8",
    )
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONPATH": str(ROOT),
            "SDLC_MANAGER_PROJECT_ID": PROJECT_ID,
            "SDLC_MANAGER_COMMAND": f"{sys.executable} {fake_cli}",
        }
    )
    process = subprocess.run(
        [sys.executable, str(ROOT / "integrations/claude-code/hook_event.py")],
        input=json.dumps(
            {
                "event_type": "PostToolUse",
                "path": "src/payments/PaymentService.py",
                "session_id": "session-1",
            }
        ).encode(),
        capture_output=True,
        cwd=ROOT,
        env=environment,
        check=False,
    )

    assert process.returncode == 20
    output = json.loads(process.stdout)
    assert output["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    assert "SDLC Manager" in output["hookSpecificOutput"]["additionalContext"]
    assert process.stderr == b"diagnostic\n"


def test_installer_is_additive_idempotent_and_selective(tmp_path: Path) -> None:
    config = tmp_path / ".kiro" / "settings" / "mcp.json"
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps({"mcpServers": {"other": {"command": "other"}}}), encoding="utf-8")
    installer = IntegrationInstaller(tmp_path)

    plan = installer.plan(["kiro"])
    assert plan["status"] == "planned"
    assert not (tmp_path / ".kiro" / "hooks" / "sdlc-manager-file-save.json").exists()

    first = installer.install(["kiro"])
    second = installer.install(["kiro"])
    assert first["status"] == "installed"
    assert second["status"] == "installed"
    installed = json.loads(config.read_text(encoding="utf-8"))
    assert "other" in installed["mcpServers"]
    assert "sdlc-manager" in installed["mcpServers"]

    removed = installer.uninstall(["kiro"])
    final = json.loads(config.read_text(encoding="utf-8"))
    assert removed["status"] == "uninstalled"
    assert final == {"mcpServers": {"other": {"command": "other"}}}


def test_codex_installer_adds_project_hooks_and_formats_context(tmp_path: Path) -> None:
    hooks_path = tmp_path / ".codex" / "hooks.json"
    hooks_path.parent.mkdir(parents=True)
    hooks_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "third-party"}]}]
                }
            }
        ),
        encoding="utf-8",
    )
    installer = IntegrationInstaller(tmp_path)
    installer.install(["codex"], project_id=PROJECT_ID)

    installed = json.loads(hooks_path.read_text(encoding="utf-8"))
    assert len(installed["hooks"]["SessionStart"]) == 1
    assert len(installed["hooks"]["PostToolUse"]) == 1
    assert len(installed["hooks"]["UserPromptSubmit"]) == 2

    fake_cli = tmp_path / "fake_cli.py"
    fake_cli.write_text(
        "import json\n"
        "print(json.dumps({'decision': 'WARN', 'recommendations': "
        "['Revisar el riesgo del componente'], 'explanation': 'Contexto disponible'}))\n",
        encoding="utf-8",
    )
    command = installed["hooks"]["PostToolUse"][0]["hooks"][0]["command"]
    assert "--project" in command
    script_tokens = shlex.split(command.split(" PostToolUse", 1)[0])
    script = script_tokens[script_tokens.index("python") + 1]
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONPATH": str(ROOT),
            "SDLC_MANAGER_COMMAND": f"{sys.executable} {fake_cli}",
        }
    )
    process = subprocess.run(
        [sys.executable, script, "PostToolUse"],
        input=json.dumps(
            {
                "hook_event_name": "PostToolUse",
                "cwd": str(tmp_path),
                "tool_use_id": "tool-1",
                "tool_input": {"file_path": "src/payments.py"},
            }
        ).encode(),
        capture_output=True,
        cwd=tmp_path,
        env=environment,
        check=False,
    )

    assert process.returncode == 0
    output = json.loads(process.stdout)
    assert output["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    assert "Revisar el riesgo del componente" in output["hookSpecificOutput"]["additionalContext"]
    assert process.stderr == b""

    installer.uninstall(["codex"])
    final = json.loads(hooks_path.read_text(encoding="utf-8"))
    assert final == {
        "hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command", "command": "third-party"}]}]}
    }
    assert not (tmp_path / ".sdlc-manager" / "providers" / "codex-plugin").exists()


def test_installer_rejects_opencode_jsonc_without_writing(tmp_path: Path) -> None:
    config = tmp_path / "opencode.jsonc"
    config.write_text('{"plugins": ["third-party"]}\n', encoding="utf-8")
    installer = IntegrationInstaller(tmp_path)

    report = installer.plan(["opencode"])

    assert report["providers"][0]["status"] == "MANUAL_MERGE_REQUIRED"
    assert config.read_text(encoding="utf-8") == '{"plugins": ["third-party"]}\n'


def test_installer_rolls_back_when_a_write_fails(tmp_path: Path, monkeypatch) -> None:
    installer = IntegrationInstaller(tmp_path)
    original_write_owned = installer._write_owned

    def fail_on_hook(path: Path, content: str, report: dict[str, object]) -> None:
        if path.name == "sdlc-manager-file-save.json":
            raise OSError("simulated write failure")
        original_write_owned(path, content, report)

    monkeypatch.setattr(installer, "_write_owned", fail_on_hook)

    with pytest.raises(OSError, match="simulated write failure"):
        installer.install(["kiro"])

    assert not (tmp_path / ".kiro" / "settings" / "mcp.json").exists()
    assert not (tmp_path / ".kiro" / "hooks").exists()
    assert not (tmp_path / ".sdlc-manager").exists()


def test_installer_cli_plan_writes_only_json_stdout(tmp_path: Path) -> None:
    environment = os.environ.copy()
    environment.update({"PYTHONPATH": str(ROOT), "SDLC_MANAGER_PROJECT_ROOT": str(tmp_path)})
    process = subprocess.run(
        [sys.executable, "-m", "sdlc_manager", "integrations", "plan", "kiro"],
        capture_output=True,
        cwd=ROOT,
        env=environment,
        check=False,
    )

    assert process.returncode == 0
    assert json.loads(process.stdout)["status"] == "planned"
    assert process.stderr == b""


def test_codex_installer_is_idempotent_and_rejects_invalid_hooks(tmp_path: Path) -> None:
    hooks_path = tmp_path / ".codex" / "hooks.json"
    installer = IntegrationInstaller(tmp_path)
    installer.install(["codex"], project_id=PROJECT_ID)
    installer.install(["codex"], project_id=PROJECT_ID)
    installed = json.loads(hooks_path.read_text(encoding="utf-8"))
    assert len(installed["hooks"]["SessionStart"]) == 1

    with pytest.raises(IntegrationError, match="hooks de Codex"):
        installer._merge_codex_hooks({"hooks": []})
    with pytest.raises(IntegrationError, match="hooks.SessionStart"):
        installer._merge_codex_hooks({"hooks": {"SessionStart": {}}})


def test_remove_hooks_ignores_missing_or_unrelated_files(tmp_path: Path) -> None:
    installer = IntegrationInstaller(tmp_path)
    report: dict = {}
    missing = tmp_path / "missing.json"
    installer._remove_codex_hooks(missing, report)
    installer._remove_json_hooks(missing, report)

    unrelated = tmp_path / "hooks.json"
    unrelated.write_text(json.dumps({"hooks": {"A": "x", "B": [{"c": 1}]}}), encoding="utf-8")
    installer._remove_json_hooks(unrelated, report)
    no_hooks = tmp_path / "other.json"
    no_hooks.write_text(json.dumps({"hooks": []}), encoding="utf-8")
    installer._remove_codex_hooks(no_hooks, report)

    assert json.loads(unrelated.read_text(encoding="utf-8")) == {
        "hooks": {"A": "x", "B": [{"c": 1}]}
    }


def test_remove_codex_hooks_drops_empty_hooks_section(tmp_path: Path) -> None:
    installer = IntegrationInstaller(tmp_path)
    installer.install(["codex"], project_id=PROJECT_ID)
    hooks_path = tmp_path / ".codex" / "hooks.json"

    installer.uninstall(["codex"])

    assert not hooks_path.exists() or "hooks" not in json.loads(
        hooks_path.read_text(encoding="utf-8")
    )
