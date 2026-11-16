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

    assert hook["version"] == "v1"
    assert hook["hooks"][0]["trigger"] == "PostFileSave"
    assert hook["hooks"][0]["enabled"] is False


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


def test_kiro_adapter_translates_payload_and_keeps_stdout_json(tmp_path: Path) -> None:
    fake_cli = tmp_path / "fake_cli.py"
    fake_cli.write_text(
        "import json, sys\n"
        "payload = json.load(sys.stdin)\n"
        "print(json.dumps({'source_client': payload['source_client'], "
        "'event_type': payload['event_type']}))\n"
        "print('adapter stderr', file=sys.stderr)\n"
        "raise SystemExit(20)\n"
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
        input=json.dumps({"path": "artifacts/sample.artifact", "session_id": "s-1"}).encode(),
        capture_output=True,
        cwd=ROOT,
        env=environment,
        check=False,
    )

    assert process.returncode == 20
    assert json.loads(process.stdout) == {
        "source_client": "kiro",
        "event_type": "file_changed",
    }
    assert process.stderr == b"adapter stderr\n"


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
