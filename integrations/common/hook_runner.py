from __future__ import annotations

import json
import os
import re
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from .event_adapter import MAX_EVENT_BYTES, project_id_from_environment, stable_event_id
from .process_event import run_normalized_event, write_adapter_error


def run_native_event(
    source_client: str,
    output_formatter: Callable[[dict[str, Any]], str] | None = None,
    default_event_type: str | None = None,
    require_affected_files: bool = False,
    exit_code_formatter: Callable[[int], int] | None = None,
) -> int:
    raw = sys.stdin.buffer.read(MAX_EVENT_BYTES + 1)
    if len(raw) > MAX_EVENT_BYTES:
        return write_adapter_error("INPUT_TOO_LARGE", "La entrada supera el limite permitido")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return write_adapter_error("INVALID_JSON", "La entrada no contiene JSON valido")
    if not isinstance(payload, dict):
        return write_adapter_error("INVALID_EVENT", "El evento debe ser un objeto JSON")
    try:
        event = normalize_native_event(payload, source_client, default_event_type)
        if require_affected_files and not event["affected_files"]:
            raise ValueError("el evento requiere al menos un archivo afectado")
    except ValueError as error:
        return write_adapter_error("INVALID_EVENT", str(error))
    original = sys.stdin
    try:
        sys.stdin = _JsonInput(event)
        return run_normalized_event(source_client, output_formatter, exit_code_formatter)
    finally:
        sys.stdin = original


def normalize_native_event(
    payload: Mapping[str, Any], source_client: str, default_event_type: str | None = None
) -> dict[str, Any]:
    event_type = _event_type(payload, default_event_type)
    files = _files(payload)
    context = _context(payload)
    project_id = _first_text(payload, "project_id", "projectId") or project_id_from_environment()
    if not project_id:
        raise ValueError("SDLC_MANAGER_PROJECT_ID es obligatorio")
    identity = _first_text(
        payload, "event_id", "eventId", "hook_event_id", "tool_use_id", "session_id", "sessionId"
    )
    timestamp = _first_text(payload, "timestamp", "time") or "1970-01-01T00:00:00Z"
    identity = identity or f"{event_type}:{timestamp}:{','.join(files)}:{source_client}"
    event: dict[str, Any] = {
        "event_id": stable_event_id(source_client, event_type, identity, payload.get("event_id")),
        "event_type": event_type,
        "source_client": source_client,
        "project_id": project_id,
        "timestamp": timestamp,
        "affected_files": files,
        "context": context,
        "schema_version": "1.0",
    }
    stage = _first_text(payload, "stage")
    if stage:
        event["stage"] = stage
    story_id = _first_text(payload, "user_story_id", "userStoryId")
    if story_id:
        event["user_story_id"] = story_id
    return event


def _event_type(payload: Mapping[str, Any], default_event_type: str | None = None) -> str:
    raw = (_first_text(payload, "event_type", "eventType", "hook_event_name", "type") or "").lower()
    raw = raw or (default_event_type or "").lower()
    mapping = {
        "sessionstart": "session_started",
        "session_start": "session_started",
        "session.started": "session_started",
        "userpromptsubmit": "session_started",
        "filechanged": "file_changed",
        "postfilesave": "file_changed",
        "file_save": "file_changed",
        "posttooluse": "file_changed",
        "tool.execute.after": "file_changed",
        "taskcompleted": "task_completed",
        "task_completed": "task_completed",
        "subagentstop": "task_completed",
        "stop": "task_completed",
    }
    event_type = mapping.get(raw, raw)
    supported = {
        "session_started",
        "file_changed",
        "task_completed",
        "incident_recorded",
    }
    if event_type not in supported:
        raise ValueError(f"evento no soportado: {raw or 'vacio'}")
    return event_type


def _files(payload: Mapping[str, Any], project_root: Path | None = None) -> list[str]:
    root_value = _first_text(payload, "project_root", "projectRoot", "cwd")
    root = Path(root_value).resolve() if root_value else project_root
    values: list[str] = []
    for key in ("path", "file_path", "filePath"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            normalized = _normalize_file_path(value, root)
            if normalized:
                values.append(normalized)
    nested = payload.get("tool_input") or payload.get("toolInput") or payload.get("input")
    if isinstance(nested, dict):
        values.extend(_files(nested, root))
    raw_files = payload.get("files")
    if isinstance(raw_files, list):
        for item in raw_files:
            if isinstance(item, str):
                normalized = _normalize_file_path(item, root)
                if normalized:
                    values.append(normalized)
    command = payload.get("command")
    if isinstance(command, str):
        for match in re.finditer(
            r"^\*\*\* (?:Update|Add|Delete) File:\s+(.+?)\s*$",
            command,
            re.MULTILINE,
        ):
            normalized = _normalize_file_path(match.group(1), root)
            if normalized:
                values.append(normalized)
    return list(dict.fromkeys(values))[:100]


def _normalize_file_path(value: str, project_root: Path | None) -> str:
    if len(value) > 500:
        raise ValueError("la ruta del archivo supera el limite permitido")
    candidate = value.replace("\\", "/")
    if os.path.isabs(value):
        if project_root is None:
            raise ValueError("las rutas absolutas requieren cwd o project_root")
        try:
            candidate = Path(value).resolve().relative_to(project_root).as_posix()
        except ValueError as error:
            raise ValueError("la ruta absoluta esta fuera del proyecto") from error
    if not candidate or candidate.startswith("/") or ".." in candidate.split("/"):
        raise ValueError("la ruta del archivo no es relativa y segura")
    return candidate


def _context(payload: Mapping[str, Any]) -> dict[str, Any]:
    context: dict[str, Any] = {}
    component = _first_text(payload, "component")
    if component:
        context["component"] = component
    return context


def _first_text(payload: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


class _JsonInput:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.buffer = _Buffer(json.dumps(payload, ensure_ascii=False).encode("utf-8"))


class _Buffer:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def read(self, size: int = -1) -> bytes:
        return self.payload[:size] if size >= 0 else self.payload


def build_context_message(result: Mapping[str, Any]) -> str | None:
    """Construye el contexto de texto para los hooks nativos o devuelve None si no hay mensajes."""
    recommendations = result.get("recommendations")
    messages = (
        [item for item in recommendations if isinstance(item, str)]
        if isinstance(recommendations, list)
        else []
    )
    decision = result.get("decision")
    explanation = result.get("explanation")
    if not messages and decision in {"WARN", "BLOCK"} and isinstance(explanation, str):
        messages.append(explanation)
    if (
        not messages
        and result.get("status") in {"rejected", "unsupported", "error"}
        and isinstance(explanation, str)
    ):
        messages.append(explanation)
    if not messages:
        return None
    context = "SDLC Manager:\n- " + "\n- ".join(messages)
    if decision in {"WARN", "BLOCK"}:
        context = f"{context}\nDecision: {decision}."
    return context[:10000]
