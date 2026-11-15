from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC
from typing import Any

from ..domain.enums import EvaluationResult
from ..domain.models import GateDecision, PolicyRule
from .condition_evaluator import ConditionEvaluationError, ConditionEvaluator


class PolicyEvaluationError(ValueError):
    """Indica un error en la evaluacion de una condicion declarativa."""


@dataclass(frozen=True, slots=True)
class ApplicableRule:
    rule: PolicyRule
    reason: str


class PolicyEngine:
    """Evalua un lenguaje cerrado de condiciones sin ejecutar codigo dinamico."""

    def __init__(self, policies: list[PolicyRule]) -> None:
        self.policies = policies
        self.conditions = ConditionEvaluator()

    def list_policies(
        self, status: str | None = None, severity: str | None = None
    ) -> list[PolicyRule]:
        return [
            policy
            for policy in self.policies
            if (status is None or policy.approval_status.value == status)
            and (severity is None or policy.severity == severity)
        ]

    def applicable_rules(self, context: dict[str, Any]) -> list[ApplicableRule]:
        result: list[ApplicableRule] = []
        for policy in self.policies:
            if not policy.enabled or not self._trigger_matches(policy.trigger, context):
                continue
            if not self._scope_matches(policy.scope, context):
                continue
            if not self.evaluate_conditions(policy.conditions, context):
                continue
            result.append(ApplicableRule(policy, policy.description))
        return result

    def evaluate_conditions(self, node: dict[str, Any], context: dict[str, Any]) -> bool:
        try:
            return self.conditions.evaluate(node, context)
        except ConditionEvaluationError as error:
            raise PolicyEvaluationError(str(error)) from error

    def evaluate_gate(
        self,
        gate: str,
        context: dict[str, Any],
        evidence_by_policy: dict[str, set[str]],
        evaluation_id: Any,
        workflow_checks: set[str] | None = None,
        skipped_rule_ids: set[str] | None = None,
    ) -> GateDecision:
        from datetime import datetime

        applicable = [
            item for item in self.applicable_rules(context) if item.rule.target_gate == gate
        ]
        triggered: list[str] = []
        missing: list[str] = []
        warnings: list[str] = []
        blocking: list[str] = []
        skipped = skipped_rule_ids or set()
        for item in applicable:
            rule = item.rule
            triggered.append(rule.id)
            if rule.id in skipped or set(rule.workflow_checks).intersection(
                workflow_checks or set()
            ):
                continue
            present = evidence_by_policy.get(rule.id, set())
            rule_missing = [name for name in rule.required_evidence if name not in present]
            missing.extend(name for name in rule_missing if name not in missing)
            if (
                rule.action == "block"
                and rule.approval_status.value == "approved"
                and (not rule.required_evidence or rule_missing)
            ):
                blocking.append(rule.id)
            elif rule.action in {"warn", "recommend"} or (
                rule.action == "block" and rule.approval_status.value != "approved"
            ):
                warnings.append(rule.id)

        if blocking:
            result = EvaluationResult.BLOCK
            explanation = (
                "Faltan evidencias obligatorias para reglas aprobadas"
                if missing
                else "Una regla aprobada impide avanzar en este gate"
            )
        elif warnings or any(item.rule.action == "warn" for item in applicable):
            result = EvaluationResult.WARN
            explanation = "Existen recomendaciones o advertencias aplicables"
        else:
            result = EvaluationResult.PASS
            explanation = "No existen incumplimientos obligatorios"
        return GateDecision(
            evaluation_id=evaluation_id,
            result=result,
            gate=gate,
            triggered_rules=triggered,
            missing_evidence=missing,
            explanation=explanation,
            evaluated_at=datetime.now(UTC),
        )

    def _trigger_matches(self, trigger: dict[str, Any], context: dict[str, Any]) -> bool:
        event = trigger.get("event")
        if event and event != context.get("event"):
            return False
        stages = trigger.get("stages")
        if stages and context.get("stage") not in stages:
            return False
        extensions = trigger.get("file_extensions")
        if extensions:
            changed_files = context.get("changed_files", [])
            if not any(self._extension(path) in extensions for path in changed_files):
                return False
        components = trigger.get("components")
        if components and context.get("component") not in components:
            return False
        return True

    @staticmethod
    def _scope_matches(scope: dict[str, Any], context: dict[str, Any]) -> bool:
        allowed_components = scope.get("components")
        return not allowed_components or context.get("component") in allowed_components

    @staticmethod
    def _extension(path: str) -> str:
        return ConditionEvaluator.extension(path)
