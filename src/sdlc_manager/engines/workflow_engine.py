from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from ..domain.enums import EvaluationResult, EvidenceStatus, ReviewStatus
from ..domain.models import Evidence, SdlcException, SdlcGate
from ..domain.ports.repositories import ExceptionApprovalAuthority
from .condition_evaluator import ConditionEvaluationError, ConditionEvaluator


@dataclass(frozen=True, slots=True)
class WorkflowEvaluation:
    result: EvaluationResult
    gate: str
    missing_evidence: list[str] = field(default_factory=list)
    pending_evidence: list[str] = field(default_factory=list)
    rejected_evidence: list[str] = field(default_factory=list)
    not_applicable_checks: list[str] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    applied_exceptions: list[str] = field(default_factory=list)
    explanation: str = ""


class DenyAllExceptionApprovalAuthority:
    """Autoridad segura por defecto hasta integrar identidad confiable."""

    def is_authorized(self, exception: SdlcException) -> bool:
        return False


class WorkflowEngine:
    """Evalua los checks declarativos de un gate sin duplicar reglas de politica."""

    _EVIDENCE_CHECKS = {
        "design_evidence",
        "review_evidence",
        "test_evidence",
        "deployment_evidence",
        "closure_evidence",
    }

    def __init__(
        self,
        condition_evaluator: ConditionEvaluator | None = None,
        approval_authority: ExceptionApprovalAuthority | None = None,
    ) -> None:
        self.conditions = condition_evaluator or ConditionEvaluator()
        self.approval_authority = approval_authority or DenyAllExceptionApprovalAuthority()

    def evaluate(
        self,
        gate: SdlcGate,
        context: dict[str, Any],
        evidences: list[Evidence],
        exceptions: list[SdlcException],
        now: datetime | None = None,
    ) -> WorkflowEvaluation:
        if not gate.enabled:
            return WorkflowEvaluation(
                result=EvaluationResult.PASS,
                gate=gate.code,
                not_applicable_checks=list(gate.checks),
                findings=[{"check": check, "status": "NOT_APPLICABLE"} for check in gate.checks],
                explanation="El gate esta deshabilitado",
            )
        current = now or datetime.now(UTC)
        applicable, errors = self._gate_applicable(gate, context)
        if errors:
            return WorkflowEvaluation(
                result=EvaluationResult.BLOCK,
                gate=gate.code,
                errors=errors,
                findings=[{"status": "ERROR", "message": error} for error in errors],
                explanation="La evaluacion del workflow contiene errores",
            )
        if not applicable:
            return WorkflowEvaluation(
                result=EvaluationResult.PASS,
                gate=gate.code,
                not_applicable_checks=list(gate.checks),
                findings=[{"check": check, "status": "NOT_APPLICABLE"} for check in gate.checks],
                explanation="El gate no aplica al contexto actual",
            )
        exception = self._active_exception(gate.code, exceptions, context, current)
        if exception is not None:
            return WorkflowEvaluation(
                result=EvaluationResult.PASS,
                gate=gate.code,
                applied_exceptions=[exception.code],
                findings=[{"status": "EXCEPTION_APPLIED", "exception": exception.code}],
                explanation=f"Se aplico la excepcion autorizada {exception.code}",
            )

        missing: list[str] = []
        pending: list[str] = []
        rejected: list[str] = []
        not_applicable: list[str] = []
        findings: list[dict[str, Any]] = []
        errors_for_checks: list[str] = []
        for check in gate.checks:
            status = self._check(check, context, evidences)
            findings.append({"check": check, "status": status})
            if status == "ERROR":
                errors_for_checks.append(f"Check de workflow no soportado: {check}")
            elif status == "MISSING":
                missing.append(check)
            elif status == "PENDING":
                pending.append(check)
            elif status == "REJECTED":
                rejected.append(check)
            elif status == "NOT_APPLICABLE":
                not_applicable.append(check)

        failing = missing + pending + rejected
        if errors_for_checks:
            result = EvaluationResult.BLOCK
            explanation = "El workflow contiene checks no soportados"
        elif failing:
            result = (
                EvaluationResult.BLOCK
                if gate.required or gate.conditions
                else EvaluationResult.WARN
            )
            explanation = "Faltan controles obligatorios del workflow"
        else:
            result = EvaluationResult.PASS
            explanation = "Controles del workflow satisfechos"
        if not gate.required and failing and not gate.conditions:
            explanation = "El gate opcional requiere atencion antes de continuar"
        return WorkflowEvaluation(
            result=result,
            gate=gate.code,
            missing_evidence=missing,
            pending_evidence=pending,
            rejected_evidence=rejected,
            not_applicable_checks=not_applicable,
            findings=findings,
            errors=errors_for_checks,
            applied_exceptions=[],
            explanation=explanation,
        )

    def _gate_applicable(self, gate: SdlcGate, context: dict[str, Any]) -> tuple[bool, list[str]]:
        if not gate.conditions:
            return True, []
        if gate.conditions == {"design_required": True}:
            return bool(context.get("design_required", False)), []
        if gate.conditions == {"design_required": False}:
            return False, []
        try:
            return self.conditions.evaluate(gate.conditions, context), []
        except ConditionEvaluationError as error:
            return False, [str(error)]

    def _check(self, check: str, context: dict[str, Any], evidences: list[Evidence]) -> str:
        if check == "description_present":
            return "PASS" if context.get("description_present", False) else "MISSING"
        if check == "acceptance_criteria_present":
            return "PASS" if context.get("acceptance_criteria_present", False) else "MISSING"
        if check == "dependencies_resolved":
            return "PASS" if context.get("dependencies_resolved", False) else "MISSING"
        if check == "story_ready":
            ready = all(
                context.get(name, False)
                for name in (
                    "description_present",
                    "acceptance_criteria_present",
                    "dependencies_resolved",
                )
            )
            return "PASS" if ready else "MISSING"
        if check in self._EVIDENCE_CHECKS:
            matches = [
                evidence
                for evidence in evidences
                if evidence.evidence_type in {check, check.removesuffix("_evidence")}
            ]
            if any(item.verification_status == EvidenceStatus.VERIFIED for item in matches):
                return "PASS"
            if any(item.verification_status == EvidenceStatus.PENDING for item in matches):
                return "PENDING"
            if any(item.verification_status == EvidenceStatus.REJECTED for item in matches):
                return "REJECTED"
            return "MISSING"
        return "ERROR"

    def _active_exception(
        self,
        gate_code: str,
        exceptions: list[SdlcException],
        context: dict[str, Any],
        now: datetime,
    ) -> SdlcException | None:
        for exception in exceptions:
            if exception.gate_code != gate_code or exception.status != ReviewStatus.APPROVED:
                continue
            if (
                not exception.responsible
                or not exception.approval_source
                or not exception.approval_reference
            ):
                continue
            if exception.valid_from and now < self._utc(exception.valid_from):
                continue
            if exception.valid_until and now > self._utc(exception.valid_until):
                continue
            try:
                condition_matches = self.conditions.evaluate(exception.condition, context)
            except ConditionEvaluationError:
                continue
            if condition_matches and self.approval_authority.is_authorized(exception):
                return exception
        return None

    @staticmethod
    def _utc(value: datetime) -> datetime:
        return value if value.tzinfo else value.replace(tzinfo=UTC)
