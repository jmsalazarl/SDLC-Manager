from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from datetime import UTC, datetime
from enum import IntEnum
from pathlib import Path
from typing import BinaryIO, TextIO

from .application.event_schemas import EventProcessingResult
from .config import get_settings
from .domain.enums import EvaluationResult, EventProcessingStatus
from .infrastructure.container import build_container
from .infrastructure.database.migrations import run_migrations
from .infrastructure.integrations.installer import IntegrationError, IntegrationInstaller

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
    if args.command == "integrations":
        return _run_integrations(args, stdout, stderr)
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


def _run_integrations(args: argparse.Namespace, stdout: TextIO, stderr: TextIO) -> int:
    try:
        settings = get_settings()
        project_root = (
            Path(args.project_root).expanduser().resolve()
            if args.project_root
            else settings.project_root
        )
        installer = IntegrationInstaller(project_root, scope=args.scope)
        providers = list(args.providers)
        if args.integration_command in {"list", "status"}:
            result = installer.list_status()
            if providers:
                result["providers"] = [
                    item for item in result["providers"] if item["provider"] in providers
                ]
        elif args.integration_command == "plan":
            result = installer.plan(providers)
        elif args.integration_command == "install":
            result = installer.install(providers, project_id=args.project_id)
        else:
            result = installer.uninstall(providers)
        if result.get("status") == "partial":
            return _write_integration_result(result, stdout, 40)
        return _write_integration_result(result, stdout, 0)
    except (IntegrationError, OSError, ValueError) as error:
        stderr.write(f"sdlc-manager: integracion rechazada: {error}\n")
        result = {
            "status": "rejected",
            "error_code": "INTEGRATION_REJECTED",
            "explanation": str(error),
        }
        return _write_integration_result(result, stdout, 40)


def _write_integration_result(result: dict[str, object], stdout: TextIO, code: int) -> int:
    stdout.write(
        json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    )
    stdout.flush()
    return code


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
    integrations = commands.add_parser(
        "integrations", help="Administra integraciones de proveedores"
    )
    integration_commands = integrations.add_subparsers(dest="integration_command", required=True)
    for name, help_text in (
        ("list", "Lista el estado de las integraciones"),
        ("plan", "Genera un plan sin modificar archivos"),
        ("install", "Instala recursos propios de SDLC Manager"),
        ("uninstall", "Retira solamente recursos propios"),
    ):
        command = integration_commands.add_parser(name, help=help_text)
        command.add_argument(
            "providers", nargs="*", choices=("codex", "kiro", "opencode", "claude-code")
        )
        command.add_argument("--scope", choices=("project", "user"), default="project")
        command.add_argument("--project-id")
        command.add_argument("--project-root")
    status = integration_commands.add_parser(
        "status", help="Muestra el estado de las integraciones"
    )
    status.add_argument(
        "providers", nargs="*", choices=("codex", "kiro", "opencode", "claude-code")
    )
    status.add_argument("--scope", choices=("project", "user"), default="project")
    status.add_argument("--project-id")
    status.add_argument("--project-root")
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
