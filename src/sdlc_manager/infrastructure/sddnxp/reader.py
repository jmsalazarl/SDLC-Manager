from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class SddnxpReader:
    """Lee metadatos locales de SDDNXP sin ejecutar comandos ni escribir."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()

    def read(self) -> dict[str, Any] | None:
        sdd_root = self.project_root / ".sdd"
        config_path = sdd_root / "config.yaml"
        if not config_path.is_file():
            return None
        try:
            config = self._load_mapping(config_path)
            specs = self._read_specs(sdd_root / "specs")
        except (OSError, ValueError, yaml.YAMLError):
            return {
                "status": "unavailable",
                "reason": "invalid_or_unreadable_configuration",
            }
        return {
            "status": "available",
            "project_id": str(config.get("projectId", "")),
            "project_name": str(config.get("projectName", "")),
            "schema_version": str(config.get("schemaVersion", "")),
            "spec_count": len(specs),
            "specs": specs,
        }

    @staticmethod
    def _load_mapping(path: Path) -> dict[str, Any]:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        if loaded is None:
            return {}
        if not isinstance(loaded, dict):
            raise ValueError("SDDNXP config must be an object")
        return loaded

    def _read_specs(self, specs_root: Path) -> list[dict[str, str | bool]]:
        if not specs_root.is_dir():
            return []
        result: list[dict[str, str | bool]] = []
        for spec_dir in sorted(item for item in specs_root.iterdir() if item.is_dir()):
            path = spec_dir / "spec.yaml"
            if not path.is_file():
                continue
            data = self._load_mapping(path)
            result.append(
                {
                    "spec_id": str(data.get("specId", "")),
                    "name": str(data.get("name", "")),
                    "version": str(data.get("version", "")),
                    "status": str(data.get("status", "")),
                    "requirements_present": (spec_dir / "requirements.md").is_file(),
                    "design_present": (spec_dir / "design.md").is_file(),
                    "tasks_present": (spec_dir / "tasks.md").is_file(),
                }
            )
        return result
