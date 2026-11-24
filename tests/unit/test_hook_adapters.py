from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest
from integrations.common import hook_runner
from integrations.common.hook_runner import (
    build_context_message,
    normalize_native_event,
    run_native_event,
)
from integrations.kiro import kiro_event_adapter

ROOT = Path(__file__).parents[2]


def load_codex_module(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    # Evita crear __pycache__ dentro del asset que el instalador copia al proyecto.
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    path = ROOT / "integrations" / "codex" / "plugin" / "hooks" / "event.py"
    spec = importlib.util.spec_from_file_location("codex_event_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_claude_module(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    path = ROOT / "integrations" / "claude-code" / "hook_event.py"
    spec = importlib.util.spec_from_file_location("claude_event_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_context_message_uses_recommendations_and_decision() -> None:
    result = {"recommendations": ["Revisar diseno", 5], "decision": "WARN"}

    assert build_context_message(result) == ("SDLC Manager:\n- Revisar diseno\nDecision: WARN.")


def test_build_context_message_falls_back_to_explanation() -> None:
    assert build_context_message({"decision": "BLOCK", "explanation": "Falta evidencia"}) == (
        "SDLC Manager:\n- Falta evidencia\nDecision: BLOCK."
    )
    assert build_context_message({"status": "error", "explanation": "Fallo"}) == (
        "SDLC Manager:\n- Fallo"
    )


def test_build_context_message_returns_none_without_messages() -> None:
    assert build_context_message({"decision": "ALLOW", "recommendations": []}) is None
    assert build_context_message({"decision": "WARN", "explanation": 3}) is None


def test_normalize_reads_project_id_from_payload_project_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("SDLC_MANAGER_PROJECT_ID", raising=False)
    config = tmp_path / ".sdlc-manager" / "config.json"
    config.parent.mkdir()
    config.write_text('{"project_id":"00e57f27-4f4c-47d0-be96-84f1b7162a99"}\n', encoding="utf-8")

    event = normalize_native_event(
        {"type": "file_changed", "path": "src/a.py", "project_root": str(tmp_path)},
        "codex",
    )

    assert event["project_id"] == "00e57f27-4f4c-47d0-be96-84f1b7162a99"


def test_claude_formatter_exposes_recommendation_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_claude_module(monkeypatch)
    output = json.loads(
        module.format_claude_output(
            {"recommendations": ["Revisar pagos"], "decision": "WARN"}, "PostToolUse"
        )
    )

    assert output["hookSpecificOutput"]["additionalContext"] == (
        "SDLC Manager:\n- Revisar pagos\nDecision: WARN."
    )


def test_kiro_formatters() -> None:
    assert kiro_event_adapter.format_kiro_output({}) == ""
    assert kiro_event_adapter.format_kiro_output({"recommendations": ["a"]}) == (
        "SDLC Manager:\n- a\n"
    )
    assert kiro_event_adapter.format_kiro_exit_code(10) == 0
    assert kiro_event_adapter.format_kiro_exit_code(0) == 0
    assert kiro_event_adapter.format_kiro_exit_code(2) == 2


def test_codex_formatter_and_main(monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_codex_module(monkeypatch)

    assert module.format_codex_output({}, "SessionStart") == "{}\n"
    output = json.loads(module.format_codex_output({"recommendations": ["a"]}, "PostToolUse"))
    assert output["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    assert "a" in output["hookSpecificOutput"]["additionalContext"]

    captured: dict[str, str] = {}

    def fake_run(source: str, formatter: object) -> int:
        captured["source"] = source
        captured["output"] = formatter({"recommendations": ["x"]})  # type: ignore[operator]
        return 7

    monkeypatch.setattr(module, "run_native_event", fake_run)
    monkeypatch.setattr(sys, "argv", ["event.py", "SessionStart"])
    assert module.main() == 7
    assert captured["source"] == "codex"
    assert "SessionStart" in captured["output"]

    monkeypatch.setattr(sys, "argv", ["event.py", "Unknown"])
    module.main()
    assert "UserPromptSubmit" in captured["output"]


def test_kiro_main_requires_affected_files(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(source: str, formatter: object, **kwargs: object) -> int:
        captured.update(source=source, **kwargs)
        return 3

    monkeypatch.setattr(kiro_event_adapter, "run_native_event", fake_run)
    assert kiro_event_adapter.main() == 3
    assert captured["source"] == "kiro"
    assert captured["require_affected_files"] is True
    assert captured["default_event_type"] == "file_changed"


def test_normalize_extracts_files_from_apply_patch_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SDLC_MANAGER_PROJECT_ID", "demo")
    command = "*** Begin Patch\n*** Update File: src/a.py\n*** Add File: src/b.py\n*** End Patch"

    event = normalize_native_event(
        {"hook_event_name": "PostToolUse", "command": command, "cwd": str(ROOT)},
        "codex",
    )

    assert event["affected_files"] == ["src/a.py", "src/b.py"]


def test_normalize_uses_default_event_type(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SDLC_MANAGER_PROJECT_ID", "demo")

    event = normalize_native_event({"path": "src/a.py", "cwd": str(ROOT)}, "kiro", "file_changed")

    assert event["event_type"] == "file_changed"


class FakeStdin:
    def __init__(self, raw: bytes) -> None:
        self.buffer = io.BytesIO(raw)


def test_run_native_event_rejects_event_without_files(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("SDLC_MANAGER_PROJECT_ID", "demo")
    monkeypatch.setattr(sys, "stdin", FakeStdin(b'{"type": "file_changed"}'))

    code = run_native_event("kiro", require_affected_files=True)

    assert code != 0
    assert "archivo afectado" in capsys.readouterr().out


def test_run_native_event_passes_exit_code_formatter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SDLC_MANAGER_PROJECT_ID", "demo")
    monkeypatch.setattr(sys, "stdin", FakeStdin(b'{"type": "file_changed", "path": "a.py"}'))
    seen: dict[str, object] = {}

    def fake_run(source: str, formatter: object, exit_code_formatter: object) -> int:
        seen["exit_code_formatter"] = exit_code_formatter
        return 10

    monkeypatch.setattr(hook_runner, "run_normalized_event", fake_run)

    assert run_native_event("kiro", None, exit_code_formatter=lambda code: code + 1) == 10
    assert callable(seen["exit_code_formatter"])


def test_run_normalized_event_applies_formatters(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from integrations.common.process_event import run_normalized_event

    fake_cli = tmp_path / "fake_cli.py"
    fake_cli.write_text(
        'import sys\nsys.stdin.read()\nprint(\'{"recommendations": ["ok"]}\')\nsys.exit(10)\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("SDLC_MANAGER_COMMAND", f"{sys.executable} {fake_cli}")
    monkeypatch.setattr(sys, "stdin", FakeStdin(b'{"event_type": "file_changed"}'))

    code = run_normalized_event(
        "kiro", kiro_event_adapter.format_kiro_output, kiro_event_adapter.format_kiro_exit_code
    )

    assert code == 0
    assert "SDLC Manager:\n- ok" in capsys.readouterr().out
