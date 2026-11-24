from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .event_adapter import MAX_EVENT_BYTES

MANAGER_ROOT = next(
    (
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "pyproject.toml").is_file()
    ),
    None,
)


def run_normalized_event(
    default_source_client: str,
    output_formatter: Callable[[dict[str, Any]], str] | None = None,
    exit_code_formatter: Callable[[int], int] | None = None,
) -> int:
    """Invoca el CLI sin shell y conserva su contrato de salida."""
    raw = sys.stdin.buffer.read(MAX_EVENT_BYTES + 1)
    if len(raw) > MAX_EVENT_BYTES:
        return write_adapter_error("INPUT_TOO_LARGE", "La entrada supera el limite permitido")
    try:
        parsed: Any = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return write_adapter_error("INVALID_JSON", "La entrada no contiene JSON valido")
    if not isinstance(parsed, dict):
        return write_adapter_error("INVALID_EVENT", "El evento debe ser un objeto JSON")
    payload: dict[str, Any] = parsed
    payload["source_client"] = default_source_client
    try:
        configured_command = os.environ.get("SDLC_MANAGER_COMMAND")
        command = (
            shlex.split(configured_command)
            if configured_command
            else (
                [
                    "uv",
                    "--directory",
                    str(MANAGER_ROOT),
                    "run",
                    "--frozen",
                    "sdlc-manager",
                ]
                if MANAGER_ROOT is not None
                else ["sdlc-manager"]
            )
        )
    except ValueError:
        return write_adapter_error("ADAPTER_COMMAND_ERROR", "SDLC_MANAGER_COMMAND no es valido")
    if not command:
        return write_adapter_error("ADAPTER_COMMAND_ERROR", "SDLC_MANAGER_COMMAND esta vacio")
    try:
        result = subprocess.run(
            [*command, "event", "process", "--stdin"],
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            check=False,
        )
    except (OSError, ValueError) as error:
        sys.stderr.write(f"sdlc-manager adapter: no fue posible iniciar el CLI: {error}\n")
        return write_adapter_error("ADAPTER_EXECUTION_ERROR", "No fue posible iniciar el CLI")
    if result.stderr:
        sys.stderr.write(result.stderr)
    if output_formatter is None:
        sys.stdout.write(result.stdout)
    else:
        try:
            parsed = json.loads(result.stdout)
            if not isinstance(parsed, dict):
                raise ValueError("CLI output is not an object")
            formatted = output_formatter(parsed)
        except (json.JSONDecodeError, TypeError, ValueError):
            formatted = result.stdout
        sys.stdout.write(formatted)
    sys.stdout.flush()
    if exit_code_formatter is not None:
        return exit_code_formatter(result.returncode)
    return result.returncode


def write_adapter_error(error_code: str, explanation: str) -> int:
    payload: dict[str, Any] = {
        "event_id": None,
        "status": "rejected",
        "decision": None,
        "triggered_rules": [],
        "workflow_checks": [],
        "applicable_practices": [],
        "relevant_experiences": [],
        "recommendations": [],
        "missing_evidence": [],
        "explanation": explanation,
        "error_code": error_code,
        "retryable": False,
        "processed_at": datetime.now(UTC).isoformat(),
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()
    return 40
