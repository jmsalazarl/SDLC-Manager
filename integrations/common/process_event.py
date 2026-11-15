from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from datetime import UTC, datetime
from typing import Any

from .event_adapter import MAX_EVENT_BYTES


def run_normalized_event(default_source_client: str) -> int:
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
        command = shlex.split(
            os.environ.get("SDLC_MANAGER_COMMAND", "uv run --frozen sdlc-manager")
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
    sys.stdout.write(result.stdout)
    sys.stdout.flush()
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
        "missing_evidence": [],
        "explanation": explanation,
        "error_code": error_code,
        "retryable": False,
        "processed_at": datetime.now(UTC).isoformat(),
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()
    return 40
