from __future__ import annotations

import json
import os
from collections.abc import Mapping
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

MAX_EVENT_BYTES = 1024 * 1024


def stable_event_id(
    source_client: str, event_type: str, identity: str, candidate: Any = None
) -> str:
    """Devuelve un UUID estable sin confiar en el cliente como aprobador."""
    if isinstance(candidate, str):
        try:
            return str(UUID(candidate))
        except ValueError:
            pass
    seed = json.dumps(
        {"source_client": source_client, "event_type": event_type, "identity": identity},
        sort_keys=True,
        separators=(",", ":"),
    )
    return str(uuid5(NAMESPACE_URL, f"sdlc-manager:{seed}"))


def normalize_file_event(
    payload: Mapping[str, Any], source_client: str, project_id: str | None
) -> dict[str, Any]:
    """Convierte un payload de hook acotado a un evento de archivo."""
    path = _first_text(payload, "path", "file_path", "filePath")
    if path is None:
        raise ValueError("El payload requiere path, file_path o filePath")
    if (
        len(path) > 500
        or path.startswith(("/", "\\"))
        or ".." in path.replace("\\", "/").split("/")
    ):
        raise ValueError("La ruta del archivo no es relativa y segura")
    if not project_id:
        raise ValueError("SDLC_MANAGER_PROJECT_ID es obligatorio")
    try:
        project_uuid = str(UUID(project_id))
    except ValueError as error:
        raise ValueError("SDLC_MANAGER_PROJECT_ID no es un UUID valido") from error

    native_identity = _first_text(payload, "event_id", "hook_event_id", "tool_use_id", "session_id")
    identity = f"{native_identity or 'no-native-id'}:{path}"
    event: dict[str, Any] = {
        "event_id": stable_event_id(
            source_client, "file_changed", identity, payload.get("event_id")
        ),
        "event_type": "file_changed",
        "source_client": source_client,
        "project_id": project_uuid,
        "timestamp": _timestamp(payload.get("timestamp")),
        "affected_files": [path],
        "context": {},
        "schema_version": "1.0",
    }
    stage = _first_text(payload, "stage")
    component = _first_text(payload, "component")
    if stage:
        event["stage"] = stage
    if component:
        event["context"] = {"component": component}
    return event


def _first_text(payload: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _timestamp(value: Any) -> str:
    if isinstance(value, str) and value:
        return value
    return "1970-01-01T00:00:00Z"


def project_id_from_environment() -> str | None:
    return os.environ.get("SDLC_MANAGER_PROJECT_ID")
