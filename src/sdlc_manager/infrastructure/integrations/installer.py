from __future__ import annotations

import hashlib
import json
import os
import shlex
import shutil
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROVIDERS = ("codex", "kiro", "opencode", "claude-code")
MANAGED_MARKER = "sdlc-manager-managed"


class IntegrationError(ValueError):
    """Error seguro durante la instalacion de un proveedor."""


@dataclass(frozen=True)
class IntegrationScope:
    name: str
    root: Path


class IntegrationInstaller:
    """Planifica y aplica integraciones sin sobreescribir contenido externo."""

    def __init__(
        self, project_root: Path, scope: str = "project", home: Path | None = None
    ) -> None:
        if scope not in {"project", "user"}:
            raise IntegrationError("scope debe ser project o user")
        self.project_root = project_root.expanduser().resolve()
        self.manager_root = Path(__file__).resolve().parents[4]
        self.home = (home or Path.home()).expanduser().resolve()
        self.scope = IntegrationScope(scope, self.project_root if scope == "project" else self.home)
        self.state_root = (
            self.project_root / ".sdlc-manager"
            if scope == "project"
            else self.home / ".config" / "sdlc-manager"
        )
        self.backup_root = self.state_root / "backups" / "integrations"

    def list_status(self) -> dict[str, Any]:
        return {
            "scope": self.scope.name,
            "root": str(self.scope.root),
            "providers": [self._status(provider) for provider in PROVIDERS],
        }

    def plan(self, providers: list[str]) -> dict[str, Any]:
        selected = self._normalize_providers(providers)
        return {
            "status": "planned",
            "scope": self.scope.name,
            "root": str(self.scope.root),
            "providers": [self._plan_provider(provider) for provider in selected],
        }

    def install(self, providers: list[str], project_id: str | None = None) -> dict[str, Any]:
        selected = self._normalize_providers(providers)
        report: dict[str, Any] = {
            "status": "installed",
            "scope": self.scope.name,
            "root": str(self.scope.root),
            "actions": [],
            "backups": [],
            "warnings": [],
            "conflicts": [],
            "providers": [],
        }
        self._preflight_install(selected, project_id)
        snapshot_paths = self._install_snapshot_paths(selected)
        with tempfile.TemporaryDirectory(prefix="sdlc-manager-install-") as temporary:
            snapshot = self._snapshot_paths(snapshot_paths, Path(temporary))
            try:
                if project_id:
                    self._write_project_config(project_id, report)
                for provider in selected:
                    provider_report = self._provider_report(provider)
                    getattr(self, f"_install_{provider.replace('-', '_')}")(provider_report)
                    report["providers"].append(provider_report)
                    report["actions"].extend(provider_report["actions"])
                    report["backups"].extend(provider_report["backups"])
                    report["warnings"].extend(provider_report["warnings"])
                    report["conflicts"].extend(provider_report["conflicts"])
                self._write_manifest(selected, report)
            except Exception:
                self._restore_paths(snapshot)
                raise
        return report

    def _preflight_install(self, providers: list[str], project_id: str | None) -> None:
        if project_id:
            self._validate_project_config(project_id)
        for provider in providers:
            getattr(self, f"_preflight_{provider.replace('-', '_')}")()

    def _validate_project_config(self, project_id: str) -> None:
        try:
            from uuid import UUID

            normalized = str(UUID(project_id))
        except ValueError as error:
            raise IntegrationError("project_id no es un UUID valido") from error
        path = self.state_root / "config.json"
        if path.is_file():
            current = self._read_json(path)
            existing = current.get("project_id")
            if existing and existing != normalized:
                raise IntegrationError(".sdlc-manager/config.json ya tiene otro project_id")

    def _preflight_kiro(self) -> None:
        self._assert_owned_or_absent(
            self.scope.root / ".kiro" / "hooks" / "sdlc-manager-file-save.json"
        )
        self._assert_owned_or_absent(self.state_root / "instructions" / "kiro.md")
        self._validate_json_mutation(
            self.scope.root / ".kiro" / "settings" / "mcp.json", self._merge_kiro
        )

    def _preflight_claude_code(self) -> None:
        self._validate_json_mutation(self.scope.root / ".mcp.json", self._merge_claude_mcp)
        self._validate_json_mutation(
            self.scope.root / ".claude" / "settings.local.json", self._merge_claude_hooks
        )
        self._validate_marked_file(self.scope.root / "CLAUDE.md")

    def _preflight_opencode(self) -> None:
        if not self._opencode_json().is_file() and self._opencode_jsonc().is_file():
            raise IntegrationError("opencode.jsonc requiere merge manual; no se reescribe")
        self._validate_json_mutation(self._opencode_json(), self._merge_opencode)
        self._assert_owned_or_absent(
            self.scope.root / ".opencode" / "plugins" / "sdlc-manager" / "index.ts"
        )
        self._assert_owned_or_absent(self.state_root / "instructions" / "opencode.md")

    def _preflight_codex(self) -> None:
        source = Path(__file__).resolve().parents[4] / "integrations" / "codex" / "plugin"
        target = self.scope.root / ".sdlc-manager" / "providers" / "codex-plugin"
        if not source.is_dir():
            raise IntegrationError(f"asset de proveedor no encontrado: {source}")
        if target.exists():
            manifest = target / ".sdlc-manager.manifest"
            target_owned = manifest.is_file() and MANAGED_MARKER in manifest.read_text(
                encoding="utf-8"
            )
            existing_files = [item for item in target.rglob("*") if item.is_file()]
            if existing_files and not target_owned:
                raise IntegrationError(f"el destino contiene archivos ajenos: {target}")
        self._validate_json_mutation(
            self.scope.root / ".codex" / "hooks.json", self._merge_codex_hooks
        )

    def _install_snapshot_paths(self, providers: list[str]) -> list[Path]:
        paths = {self.state_root}
        for provider in providers:
            paths.update(self._provider_paths(provider))
        return sorted(paths, key=str)

    @staticmethod
    def _snapshot_paths(paths: list[Path], root: Path) -> list[tuple[Path, Path, bool]]:
        snapshots: list[tuple[Path, Path, bool]] = []
        for index, path in enumerate(paths):
            target = root / str(index)
            existed = path.exists()
            if existed:
                if path.is_dir():
                    shutil.copytree(path, target)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, target)
            snapshots.append((path, target, existed))
        return snapshots

    @staticmethod
    def _restore_paths(snapshots: list[tuple[Path, Path, bool]]) -> None:
        for path, snapshot, existed in reversed(snapshots):
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()
            if not existed:
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            if snapshot.is_dir():
                shutil.copytree(snapshot, path)
            else:
                shutil.copy2(snapshot, path)

    def uninstall(self, providers: list[str]) -> dict[str, Any]:
        selected = self._normalize_providers(providers)
        report: dict[str, Any] = {
            "status": "uninstalled",
            "scope": self.scope.name,
            "root": str(self.scope.root),
            "actions": [],
            "backups": [],
            "warnings": [],
            "conflicts": [],
            "providers": [],
        }
        for provider in selected:
            provider_report = self._provider_report(provider)
            try:
                getattr(self, f"_uninstall_{provider.replace('-', '_')}")(provider_report)
            except IntegrationError as error:
                provider_report["status"] = "CONFLICT"
                provider_report["conflicts"].append(str(error))
                report["status"] = "partial"
            report["providers"].append(provider_report)
            report["actions"].extend(provider_report["actions"])
            report["backups"].extend(provider_report["backups"])
            report["warnings"].extend(provider_report["warnings"])
            report["conflicts"].extend(provider_report["conflicts"])
        return report

    def _normalize_providers(self, providers: list[str]) -> list[str]:
        selected = providers or list(PROVIDERS)
        invalid = [item for item in selected if item not in PROVIDERS]
        if invalid:
            raise IntegrationError(f"proveedor no soportado: {', '.join(invalid)}")
        return list(dict.fromkeys(selected))

    def _provider_report(self, provider: str) -> dict[str, Any]:
        return {
            "provider": provider,
            "status": "IMPLEMENTED",
            "actions": [],
            "backups": [],
            "warnings": [],
            "conflicts": [],
            "verification": "NOT_VERIFIED",
        }

    def _status(self, provider: str) -> dict[str, Any]:
        paths = self._provider_paths(provider)
        existing = [str(path) for path in paths if path.exists()]
        return {
            "provider": provider,
            "status": "INSTALLED" if existing else "NOT_INSTALLED",
            "paths": [str(path) for path in paths],
            "existing": existing,
            "verification": "NOT_VERIFIED",
        }

    def _plan_provider(self, provider: str) -> dict[str, Any]:
        report = self._provider_report(provider)
        report["planned_paths"] = [str(path) for path in self._provider_paths(provider)]
        if (
            provider == "opencode"
            and self._opencode_jsonc().is_file()
            and not self._opencode_json().is_file()
        ):
            report["status"] = "MANUAL_MERGE_REQUIRED"
            report["warnings"].append("opencode.jsonc no se reescribe automaticamente")
        return report

    def _provider_paths(self, provider: str) -> list[Path]:
        root = self.scope.root
        if provider == "kiro":
            return [
                root / ".kiro" / "settings" / "mcp.json",
                root / ".kiro" / "hooks" / "sdlc-manager-file-save.json",
            ]
        if provider == "claude-code":
            return [
                root / ".mcp.json",
                root / ".claude" / "settings.local.json",
                root / "CLAUDE.md",
            ]
        if provider == "opencode":
            return [
                self._opencode_json(),
                self._opencode_jsonc(),
                root / ".opencode" / "plugins" / "sdlc-manager",
            ]
        return [
            root / ".codex" / "hooks.json",
            root / ".sdlc-manager" / "providers" / "codex-plugin",
        ]

    def _write_project_config(self, project_id: str, report: dict[str, Any]) -> None:
        if self.scope.name != "project":
            return
        try:
            from uuid import UUID

            normalized = str(UUID(project_id))
        except ValueError as error:
            raise IntegrationError("project_id no es un UUID valido") from error
        path = self.state_root / "config.json"
        current = self._read_json(path) if path.is_file() else {}
        existing = current.get("project_id")
        if existing and existing != normalized:
            raise IntegrationError(".sdlc-manager/config.json ya tiene otro project_id")
        current["project_id"] = normalized
        self._write_json(path, current, report)

    def _install_kiro(self, report: dict[str, Any]) -> None:
        config = self.scope.root / ".kiro" / "settings" / "mcp.json"
        hook = self.scope.root / ".kiro" / "hooks" / "sdlc-manager-file-save.json"
        instruction = self.state_root / "instructions" / "kiro.md"
        self._assert_owned_or_absent(hook)
        self._assert_owned_or_absent(instruction)
        self._merge_json(config, self._merge_kiro, report)
        self._write_owned(
            hook,
            self._asset(
                "integrations/kiro/hooks/sdlc-file-save.installed.json",
                {"__SDLC_MANAGER_ROOT__": self._manager_root_literal()},
            ),
            report,
        )
        self._write_owned(instruction, self._instructions(), report)

    def _install_claude_code(self, report: dict[str, Any]) -> None:
        mcp = self.scope.root / ".mcp.json"
        settings = self.scope.root / ".claude" / "settings.local.json"
        self._validate_json_mutation(mcp, self._merge_claude_mcp)
        self._validate_json_mutation(settings, self._merge_claude_hooks)
        self._validate_marked_file(self.scope.root / "CLAUDE.md")
        self._merge_json(mcp, self._merge_claude_mcp, report)
        self._merge_json(settings, self._merge_claude_hooks, report)
        self._merge_marked_file(self.scope.root / "CLAUDE.md", self._instructions(), report)

    def _install_opencode(self, report: dict[str, Any]) -> None:
        config = self._opencode_json()
        if not config.is_file() and self._opencode_jsonc().is_file():
            raise IntegrationError("opencode.jsonc requiere merge manual; no se reescribe")
        plugin = self.scope.root / ".opencode" / "plugins" / "sdlc-manager" / "index.ts"
        instruction = self.state_root / "instructions" / "opencode.md"
        self._validate_json_mutation(config, self._merge_opencode)
        self._assert_owned_or_absent(plugin)
        self._assert_owned_or_absent(instruction)
        self._merge_json(config, self._merge_opencode, report)
        self._write_owned(
            plugin,
            self._asset(
                "integrations/opencode/plugin/index.ts",
                {"__SDLC_MANAGER_ROOT__": self._manager_root_literal()},
            ),
            report,
        )
        self._write_owned(instruction, self._instructions(), report)

    def _install_codex(self, report: dict[str, Any]) -> None:
        target = self.scope.root / ".sdlc-manager" / "providers" / "codex-plugin"
        self._copy_tree(
            Path(__file__).resolve().parents[4] / "integrations" / "codex" / "plugin",
            target,
            report,
            {"__SDLC_MANAGER_ROOT__": self._manager_root_literal()},
        )
        self._write_owned(target / ".sdlc-manager.manifest", MANAGED_MARKER + "\n", report)
        self._merge_json(self.scope.root / ".codex" / "hooks.json", self._merge_codex_hooks, report)
        self._write_owned(
            self.state_root / "instructions" / "codex.md", self._instructions(), report
        )
        report["warnings"].append(
            "Codex requiere confiar los hooks del proyecto antes de ejecutarlos"
        )

    def _uninstall_kiro(self, report: dict[str, Any]) -> None:
        self._remove_json_entry(
            self.scope.root / ".kiro" / "settings" / "mcp.json",
            "mcpServers",
            "sdlc-manager",
            report,
            self._kiro_server(),
        )
        self._remove_owned(
            self.scope.root / ".kiro" / "hooks" / "sdlc-manager-file-save.json", report
        )
        self._remove_owned(self.state_root / "instructions" / "kiro.md", report)

    def _uninstall_claude_code(self, report: dict[str, Any]) -> None:
        self._remove_json_entry(
            self.scope.root / ".mcp.json",
            "mcpServers",
            "sdlc-manager",
            report,
            self._claude_server(),
        )
        self._remove_json_hooks(self.scope.root / ".claude" / "settings.local.json", report)
        self._remove_marked_file(self.scope.root / "CLAUDE.md", report)

    def _uninstall_opencode(self, report: dict[str, Any]) -> None:
        self._remove_opencode_config(self._opencode_json(), report)
        self._remove_owned_tree(self.scope.root / ".opencode" / "plugins" / "sdlc-manager", report)
        self._remove_owned(self.state_root / "instructions" / "opencode.md", report)

    def _uninstall_codex(self, report: dict[str, Any]) -> None:
        self._remove_codex_hooks(self.scope.root / ".codex" / "hooks.json", report)
        self._remove_owned_tree(
            self.scope.root / ".sdlc-manager" / "providers" / "codex-plugin", report
        )
        self._remove_owned(self.state_root / "instructions" / "codex.md", report)

    def _merge_kiro(self, data: dict[str, Any]) -> None:
        servers = data.setdefault("mcpServers", {})
        if not isinstance(servers, dict):
            raise IntegrationError("mcpServers de Kiro no es un objeto")
        self._set_owned_mapping(servers, "sdlc-manager", self._kiro_server())

    def _merge_claude_mcp(self, data: dict[str, Any]) -> None:
        servers = data.setdefault("mcpServers", {})
        if not isinstance(servers, dict):
            raise IntegrationError("mcpServers de Claude Code no es un objeto")
        self._set_owned_mapping(servers, "sdlc-manager", self._claude_server())

    def _merge_opencode(self, data: dict[str, Any]) -> None:
        mcp = data.setdefault("mcp", {})
        if not isinstance(mcp, dict):
            raise IntegrationError("mcp de OpenCode no es un objeto")
        servers = mcp.setdefault("servers", {})
        if not isinstance(servers, dict):
            raise IntegrationError("mcp.servers de OpenCode no es un objeto")
        self._set_owned_mapping(servers, "sdlc-manager", self._opencode_server())
        plugins = data.setdefault("plugins", [])
        plugin_path = "./.opencode/plugins/sdlc-manager"
        if not isinstance(plugins, list):
            raise IntegrationError("plugins de OpenCode no es una lista")
        if plugin_path not in plugins:
            plugins.append(plugin_path)

    def _merge_codex_hooks(self, data: dict[str, Any]) -> None:
        hooks = data.setdefault("hooks", {})
        if not isinstance(hooks, dict):
            raise IntegrationError("hooks de Codex no es un objeto")
        script = (
            self.scope.root / ".sdlc-manager" / "providers" / "codex-plugin" / "hooks" / "event.py"
        )
        command = shlex.join(
            [
                "uv",
                "--project",
                str(self.manager_root),
                "run",
                "--frozen",
                "python",
                str(script),
            ]
        )
        for event_name in ("SessionStart", "UserPromptSubmit", "PostToolUse"):
            entries = hooks.setdefault(event_name, [])
            if not isinstance(entries, list):
                raise IntegrationError(f"hooks.{event_name} de Codex no es una lista")
            if any(command in json.dumps(item, sort_keys=True) for item in entries):
                continue
            entries.append(
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"{command} {event_name}",
                            "statusMessage": "Reviewing SDLC Manager context",
                            "additionalContextLimit": 1200,
                        }
                    ]
                }
            )

    def _merge_claude_hooks(self, data: dict[str, Any]) -> None:
        hooks = data.setdefault("hooks", {})
        entries = hooks.setdefault("PostToolUse", [])
        marker = "integrations/claude-code/hook_event.py"
        if not isinstance(entries, list):
            raise IntegrationError("hooks.PostToolUse no es una lista")
        if not any(marker in json.dumps(item, sort_keys=True) for item in entries):
            command = shlex.join(
                [
                    "uv",
                    "--project",
                    str(self.manager_root),
                    "run",
                    "python",
                    str(self.manager_root / "integrations/claude-code/hook_event.py"),
                    "--source",
                    "claude-code",
                    "--format",
                    "claude",
                ]
            )
            entries.append(
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": command,
                        }
                    ]
                }
            )

    @staticmethod
    def _set_owned_mapping(target: dict[str, Any], key: str, value: dict[str, Any]) -> None:
        existing = target.get(key)
        if existing is not None and existing != value:
            raise IntegrationError(f"la entrada {key} ya existe con otra configuracion")
        target[key] = value

    def _kiro_server(self) -> dict[str, Any]:
        return {
            "command": "uv",
            "args": [
                "--directory",
                str(self.manager_root),
                "run",
                "--frozen",
                "sdlc-manager",
            ],
            "disabled": False,
        }

    def _claude_server(self) -> dict[str, Any]:
        return {
            "type": "stdio",
            "command": "uv",
            "args": [
                "--directory",
                str(self.manager_root),
                "run",
                "--frozen",
                "sdlc-manager",
            ],
        }

    def _opencode_server(self) -> dict[str, Any]:
        return {
            "type": "local",
            "command": [
                "uv",
                "--directory",
                str(self.manager_root),
                "run",
                "--frozen",
                "sdlc-manager",
            ],
            "cwd": ".",
            "codemode": False,
        }

    def _merge_json(
        self, path: Path, mutator: Callable[[dict[str, Any]], None], report: dict[str, Any]
    ) -> None:
        data = self._read_json(path) if path.is_file() else {}
        mutator(data)
        self._write_json(path, data, report)

    def _validate_json_mutation(
        self, path: Path, mutator: Callable[[dict[str, Any]], None]
    ) -> None:
        data = self._read_json(path) if path.is_file() else {}
        mutator(data)

    @staticmethod
    def _validate_marked_file(path: Path) -> None:
        if not path.is_file():
            return
        content = path.read_text(encoding="utf-8")
        start = "<!-- sdlc-manager:start -->"
        end = "<!-- sdlc-manager:end -->"
        if (start in content) != (end in content):
            raise IntegrationError(f"marcadores incompletos: {path}")

    @staticmethod
    def _assert_owned_or_absent(path: Path) -> None:
        if not path.exists():
            return
        if not path.is_file():
            raise IntegrationError(f"la ruta no es un archivo regular: {path}")
        if MANAGED_MARKER not in path.read_text(encoding="utf-8"):
            raise IntegrationError(f"no se sobreescribe un archivo ajeno: {path}")

    def _read_json(self, path: Path) -> dict[str, Any]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise IntegrationError(f"no se puede leer JSON de forma segura: {path}") from error
        if not isinstance(data, dict):
            raise IntegrationError(f"la configuracion debe ser un objeto JSON: {path}")
        return data

    def _write_json(self, path: Path, value: dict[str, Any], report: dict[str, Any]) -> None:
        self._write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n", report)

    def _write_owned(self, path: Path, content: str, report: dict[str, Any]) -> None:
        if path.is_file():
            current = path.read_text(encoding="utf-8")
            if current != content and MANAGED_MARKER not in current:
                raise IntegrationError(f"no se sobreescribe un archivo ajeno: {path}")
        self._write_text(path, content, report)

    def _write_text(self, path: Path, content: str, report: dict[str, Any]) -> None:
        if path.is_file() and path.read_text(encoding="utf-8") == content:
            report["actions"].append({"path": str(path), "status": "unchanged"})
            return
        if path.exists() and not path.is_file():
            raise IntegrationError(f"la ruta no es un archivo regular: {path}")
        if path.is_file():
            report["backups"].append(self._backup(path))
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, delete=False
        ) as temp:
            temp.write(content)
            temp.flush()
            os.fsync(temp.fileno())
            temporary = Path(temp.name)
        os.replace(temporary, path)
        report["actions"].append({"path": str(path), "status": "written"})

    def _backup(self, path: Path) -> str:
        digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:12]
        target = self.backup_root / f"{digest}-{path.name}"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        return str(target)

    def _merge_marked_file(self, path: Path, content: str, report: dict[str, Any]) -> None:
        start = "<!-- sdlc-manager:start -->"
        end = "<!-- sdlc-manager:end -->"
        existing = path.read_text(encoding="utf-8") if path.is_file() else ""
        if (start in existing) != (end in existing):
            raise IntegrationError(f"marcadores incompletos: {path}")
        if start in existing:
            before = existing.split(start, 1)[0].rstrip()
            after = existing.split(end, 1)[1].lstrip()
            existing = (before + "\n\n" + after).strip()
        block = f"{start}\n\n{content.strip()}\n\n{end}\n"
        self._write_text(path, (existing + "\n\n" if existing else "") + block, report)

    def _remove_marked_file(self, path: Path, report: dict[str, Any]) -> None:
        if not path.is_file():
            return
        content = path.read_text(encoding="utf-8")
        start = "<!-- sdlc-manager:start -->"
        end = "<!-- sdlc-manager:end -->"
        if start not in content and end not in content:
            return
        if (start in content) != (end in content):
            raise IntegrationError(f"marcadores incompletos: {path}")
        before = content.split(start, 1)[0].rstrip()
        after = content.split(end, 1)[1].lstrip()
        self._write_text(
            path, ((before + "\n\n" + after).strip() + "\n") if before or after else "", report
        )

    def _remove_json_entry(
        self, path: Path, parent: str, key: str, report: dict[str, Any], expected: dict[str, Any]
    ) -> None:
        if not path.is_file():
            return
        data = self._read_json(path)
        entries = data.get(parent)
        if not isinstance(entries, dict) or key not in entries:
            return
        if entries[key] != expected:
            raise IntegrationError(f"no se retira una entrada ajena: {path}:{key}")
        del entries[key]
        self._write_json(path, data, report)

    def _remove_json_hooks(self, path: Path, report: dict[str, Any]) -> None:
        if not path.is_file():
            return
        data = self._read_json(path)
        hooks = data.get("hooks")
        if not isinstance(hooks, dict):
            return
        changed = False
        for name, entries in list(hooks.items()):
            if not isinstance(entries, list):
                continue
            filtered = [
                item
                for item in entries
                if "integrations/claude-code/hook_event.py" not in json.dumps(item)
            ]
            changed = changed or len(filtered) != len(entries)
            if filtered:
                hooks[name] = filtered
            elif name in hooks:
                del hooks[name]
        if changed:
            self._write_json(path, data, report)

    def _remove_codex_hooks(self, path: Path, report: dict[str, Any]) -> None:
        if not path.is_file():
            return
        data = self._read_json(path)
        hooks = data.get("hooks")
        if not isinstance(hooks, dict):
            return
        script = (
            self.scope.root / ".sdlc-manager" / "providers" / "codex-plugin" / "hooks" / "event.py"
        )
        marker = str(script)
        changed = False
        for name, entries in list(hooks.items()):
            if not isinstance(entries, list):
                continue
            filtered = [item for item in entries if marker not in json.dumps(item, sort_keys=True)]
            changed = changed or len(filtered) != len(entries)
            if filtered:
                hooks[name] = filtered
            else:
                del hooks[name]
        if changed:
            if not hooks:
                data.pop("hooks", None)
            self._write_json(path, data, report)

    def _remove_opencode_config(self, path: Path, report: dict[str, Any]) -> None:
        if not path.is_file():
            return
        data = self._read_json(path)
        mcp = data.get("mcp")
        changed = False
        if isinstance(mcp, dict) and isinstance(mcp.get("servers"), dict):
            servers = mcp["servers"]
            if servers.get("sdlc-manager") == self._opencode_server():
                del servers["sdlc-manager"]
                changed = True
        plugins = data.get("plugins")
        if isinstance(plugins, list):
            filtered = [item for item in plugins if item != "./.opencode/plugins/sdlc-manager"]
            changed = changed or len(filtered) != len(plugins)
            data["plugins"] = filtered
        if changed:
            self._write_json(path, data, report)

    def _remove_owned(self, path: Path, report: dict[str, Any]) -> None:
        if not path.is_file():
            return
        if MANAGED_MARKER not in path.read_text(encoding="utf-8"):
            raise IntegrationError(f"archivo no identificado como propio: {path}")
        report["backups"].append(self._backup(path))
        path.unlink()
        report["actions"].append({"path": str(path), "status": "removed"})

    def _remove_owned_tree(self, path: Path, report: dict[str, Any]) -> None:
        if not path.exists():
            return
        if not path.is_dir():
            raise IntegrationError(f"la integracion no es un directorio: {path}")
        manifest = path / ".sdlc-manager.manifest"
        files = [item for item in path.rglob("*") if item.is_file()]
        if not files:
            raise IntegrationError(f"el directorio no contiene una marca de propiedad: {path}")
        owned_tree = manifest.is_file() and MANAGED_MARKER in manifest.read_text(encoding="utf-8")
        unowned = any(MANAGED_MARKER not in item.read_text(encoding="utf-8") for item in files)
        if not owned_tree and unowned:
            raise IntegrationError(
                f"el directorio contiene archivos no identificados como propios: {path}"
            )
        for item in sorted(files, reverse=True):
            if item.is_file():
                report["backups"].append(self._backup(item))
                item.unlink()
        for item in sorted(path.rglob("*"), reverse=True):
            if item.is_dir():
                item.rmdir()
        path.rmdir()
        report["actions"].append({"path": str(path), "status": "removed"})

    def _copy_tree(
        self,
        source: Path,
        target: Path,
        report: dict[str, Any],
        replacements: dict[str, str] | None = None,
    ) -> None:
        if not source.is_dir():
            raise IntegrationError(f"asset de proveedor no encontrado: {source}")
        manifest = target / ".sdlc-manager.manifest"
        target_owned = manifest.is_file() and MANAGED_MARKER in manifest.read_text(encoding="utf-8")
        if target.exists() and not target_owned:
            existing_files = [item for item in target.rglob("*") if item.is_file()]
            if existing_files:
                raise IntegrationError(f"el destino contiene archivos ajenos: {target}")
        for item in sorted(source.rglob("*")):
            relative = item.relative_to(source)
            destination = target / relative
            if item.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
            else:
                content = item.read_text(encoding="utf-8")
                for old, new in (replacements or {}).items():
                    content = content.replace(old, new)
                if target_owned:
                    self._write_text(destination, content, report)
                else:
                    self._write_owned(destination, content, report)

    def _write_manifest(self, providers: list[str], report: dict[str, Any]) -> None:
        path = self.state_root / "integrations.json"
        current = self._read_json(path) if path.is_file() else {}
        current["managed_by"] = MANAGED_MARKER
        current["providers"] = providers
        self._write_owned(path, json.dumps(current, indent=2, sort_keys=True) + "\n", report)

    def _opencode_json(self) -> Path:
        return self.scope.root / "opencode.json"

    def _opencode_jsonc(self) -> Path:
        return self.scope.root / "opencode.jsonc"

    @staticmethod
    def _instructions() -> str:
        return (
            "<!-- sdlc-manager-managed -->\n\n"
            "# SDLC Manager\n\n"
            "Consulta SDLC Manager cuando cambie un componente, inicie una tarea "
            "o evalúe un gate. Muestra WARN y no lo conviertas en BLOCK. "
            "decision null, rechazos y errores no son PASS.\n"
        )

    @staticmethod
    def _asset(relative: str, replacements: dict[str, str] | None = None) -> str:
        root = Path(__file__).resolve().parents[4]
        content = (root / relative).read_text(encoding="utf-8")
        for old, new in (replacements or {}).items():
            content = content.replace(old, new)
        return content

    def _manager_root_literal(self) -> str:
        return str(self.manager_root).replace("\\", "\\\\").replace('"', '\\"')
