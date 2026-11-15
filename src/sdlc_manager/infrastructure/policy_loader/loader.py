from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ...domain.enums import PolicyApprovalStatus
from ...domain.models import PolicyRule


class PolicyLoadError(ValueError):
    """Indica que un archivo de politicas no cumple el contrato."""


class PolicyYamlModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    version: str = Field(min_length=1, max_length=40)
    severity: str = Field(pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    trigger: dict[str, Any]
    scope: dict[str, Any] = Field(default_factory=dict)
    conditions: dict[str, Any] = Field(default_factory=dict)
    required_evidence: list[str] = Field(default_factory=list)
    target_gate: str = Field(min_length=1, max_length=80)
    action: str = Field(pattern="^(recommend|warn|block)$")
    approval_status: str = Field(pattern="^(draft|approved|rejected)$")
    workflow_checks: list[str] = Field(default_factory=list)
    enabled: bool = True


class PolicyLoader:
    def __init__(self, paths: list[Path]) -> None:
        self.paths = paths

    def load(self) -> list[PolicyRule]:
        policies: list[PolicyRule] = []
        seen_ids: set[str] = set()
        for root in self.paths:
            if not root.exists():
                continue
            files = [root] if root.is_file() else sorted(root.rglob("*.yaml"))
            for path in files:
                if path.suffix not in {".yaml", ".yml"}:
                    continue
                policy = self._load_file(path)
                if policy.id in seen_ids:
                    raise PolicyLoadError(f"Politica duplicada: {policy.id}")
                seen_ids.add(policy.id)
                policies.append(
                    PolicyRule(
                        id=policy.id,
                        name=policy.name,
                        description=policy.description,
                        version=policy.version,
                        severity=policy.severity,
                        trigger=policy.trigger,
                        scope=policy.scope,
                        conditions=policy.conditions,
                        required_evidence=policy.required_evidence,
                        target_gate=policy.target_gate,
                        action=policy.action,
                        approval_status=PolicyApprovalStatus(policy.approval_status),
                        workflow_checks=policy.workflow_checks,
                        enabled=policy.enabled,
                    )
                )
        return policies

    @staticmethod
    def _load_file(path: Path) -> PolicyYamlModel:
        try:
            content = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(content, dict):
                raise PolicyLoadError(f"El archivo {path} debe contener un objeto YAML")
            return PolicyYamlModel.model_validate(content)
        except (OSError, yaml.YAMLError, ValidationError) as error:
            raise PolicyLoadError(f"Politica invalida en {path}: {error}") from error
