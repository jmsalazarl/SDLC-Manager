from __future__ import annotations

from pathlib import PurePosixPath

_GENERIC_ROOTS = {
    "app",
    "apps",
    "components",
    "lib",
    "libs",
    "modules",
    "packages",
    "services",
    "src",
}


def infer_component(files: list[str]) -> str | None:
    """Infere un componente desde rutas relativas sin leer el filesystem."""
    for value in files:
        path = PurePosixPath(value.replace("\\", "/"))
        parts = [part for part in path.parts if part not in {".", ""}]
        if not parts:
            continue
        candidate = parts[0]
        if candidate in _GENERIC_ROOTS and len(parts) > 1:
            candidate = parts[1]
        if candidate and candidate not in {"tests", "test", "docs", "migrations"}:
            return candidate
    return None


def resolve_component(context: dict[str, object], files: list[str]) -> str | None:
    """Prefiere el componente declarado y usa la ruta como fallback acotado."""
    declared = context.get("component")
    if isinstance(declared, str) and declared.strip():
        return declared.strip()
    return infer_component(files)
