from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from datetime import UTC, datetime
from enum import IntEnum
from typing import BinaryIO, TextIO

from .application.event_schemas import EventProcessingResult
from .config import get_settings
from .domain.enums import EvaluationResult, EventProcessingStatus
from .infrastructure.container import build_container
from .infrastructure.database.migrations import run_migrations

MAX_STDIN_BYTES = 1024 * 1024


class CliExitCode(IntEnum):
    INFO = 0
    PASS = 10
    WARN = 20
    BLOCK = 30
    REJECTED = 40
    ERROR_FATAL = 50
    ERROR_RETRYABLE = 51


def run_cli(
    argv: Sequence[str],
    stdin: BinaryIO,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    args = _build_parser().parse_args(list(argv))
    if not args.stdin:
        return _write_result(
            _result(
                EventProcessingStatus.REJECTED,
                "El modo de entrada debe ser stdin",
                "INVALID_ARGUMENTS",
            ),
            stdout,
        )

    payload, input_error = _read_payload(stdin)
    if input_error is not None:
        return _write_result(input_error, stdout)

    try:
        settings = get_settings()
        if settings.auto_migrate:
            run_migrations(settings)
        container = build_container(settings, initialize_schema=False)
        result = container.event_processor.process_payload(payload)
    except Exception:
        stderr.write("sdlc-manager: no fue posible inicializar el almacenamiento local\n")
        result = _result(
            EventProcessingStatus.ERROR,
            "No fue posible inicializar el almacenamiento local",
            "CLI_BOOTSTRAP_ERROR",
        )
    return _write_result(result, stdout)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sdlc-manager")
    commands = parser.add_subparsers(dest="command", required=True)
    event = commands.add_parser("event", help="Procesa eventos normalizados del SDLC")
    event_commands = event.add_subparsers(dest="event_command", required=True)
    process = event_commands.add_parser("process", help="Procesa un evento")
    process.add_argument(
        "--stdin",
        action="store_true",
        required=True,
        help="Lee un unico evento JSON desde stdin",
    )
    return parser


def _read_payload(stdin: BinaryIO) -> tuple[object | None, EventProcessingResult | None]:
    raw = stdin.read(MAX_STDIN_BYTES + 1)
    if len(raw) > MAX_STDIN_BYTES:
        return None, _result(
            EventProcessingStatus.REJECTED,
            "La entrada supera el limite permitido",
            "INPUT_TOO_LARGE",
        )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None, _result(
            EventProcessingStatus.REJECTED,
            "La entrada no es UTF-8 valida",
            "INVALID_UTF8",
        )
    try:
        return json.loads(text), None
    except json.JSONDecodeError:
        return None, _result(
            EventProcessingStatus.REJECTED,
            "La entrada no contiene JSON valido",
            "INVALID_JSON",
        )


def _result(
    status: EventProcessingStatus,
    explanation: str,
    error_code: str,
) -> EventProcessingResult:
    return EventProcessingResult(
        event_id=None,
        status=status,
        decision=None,
        explanation=explanation,
        error_code=error_code,
        retryable=False,
        processed_at=datetime.now(UTC),
    )


def _write_result(result: EventProcessingResult, stdout: TextIO) -> int:
    payload = json.dumps(
        result.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    stdout.write(f"{payload}\n")
    stdout.flush()
    return _exit_code(result)


def _exit_code(result: EventProcessingResult) -> int:
    if result.status in {
        EventProcessingStatus.REJECTED,
        EventProcessingStatus.UNSUPPORTED,
    }:
        return int(CliExitCode.REJECTED)
    if result.status == EventProcessingStatus.ERROR:
        return int(CliExitCode.ERROR_RETRYABLE if result.retryable else CliExitCode.ERROR_FATAL)
    if result.decision == EvaluationResult.PASS:
        return int(CliExitCode.PASS)
    if result.decision == EvaluationResult.WARN:
        return int(CliExitCode.WARN)
    if result.decision == EvaluationResult.BLOCK:
        return int(CliExitCode.BLOCK)
    return int(CliExitCode.INFO)
