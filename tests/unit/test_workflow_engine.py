from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sdlc_manager.domain.enums import EvaluationResult, EvidenceStatus, ReviewStatus
from sdlc_manager.domain.models import Evidence, SdlcException, SdlcGate
from sdlc_manager.engines.workflow_engine import WorkflowEngine


def make_gate(
    code: str,
    checks: list[str],
    required: bool = True,
    conditions: dict | None = None,
) -> SdlcGate:
    return SdlcGate(
        id=uuid4(),
        stage_id=uuid4(),
        code=code,
        name=code,
        required=required,
        checks=checks,
        conditions=conditions or {},
        enabled=True,
    )


def evidence(evidence_type: str, status: EvidenceStatus) -> Evidence:
    return Evidence(
        id=uuid4(),
        project_id=uuid4(),
        user_story_id=uuid4(),
        policy_id="WORKFLOW",
        evidence_type=evidence_type,
        reference="record:test",
        verification_status=status,
        verified_by="reviewer" if status != EvidenceStatus.PENDING else None,
        verified_at=None,
    )


def test_workflow_checks_and_evidence_statuses() -> None:
    engine = WorkflowEngine()
    gate = make_gate("testing_complete", ["test_evidence"])

    missing = engine.evaluate(gate, {}, [], [])
    pending = engine.evaluate(gate, {}, [evidence("test_evidence", EvidenceStatus.PENDING)], [])
    rejected = engine.evaluate(gate, {}, [evidence("test_evidence", EvidenceStatus.REJECTED)], [])
    passed = engine.evaluate(gate, {}, [evidence("test_evidence", EvidenceStatus.VERIFIED)], [])

    assert missing.result == EvaluationResult.BLOCK
    assert missing.missing_evidence == ["test_evidence"]
    assert pending.pending_evidence == ["test_evidence"]
    assert rejected.rejected_evidence == ["test_evidence"]
    assert passed.result == EvaluationResult.PASS


def test_design_gate_is_not_applicable_without_design_requirement() -> None:
    engine = WorkflowEngine()
    gate = make_gate(
        "design_approved",
        ["design_evidence"],
        required=False,
        conditions={"design_required": True},
    )

    not_required = engine.evaluate(gate, {"design_required": False}, [], [])
    required = engine.evaluate(gate, {"design_required": True}, [], [])

    assert not_required.result == EvaluationResult.PASS
    assert not_required.not_applicable_checks == ["design_evidence"]
    assert required.result == EvaluationResult.BLOCK


def test_pending_or_untrusted_exception_never_bypasses_gate() -> None:
    engine = WorkflowEngine()
    gate = make_gate("task_completion", ["closure_evidence"])
    base = dict(
        id=uuid4(),
        workflow_id=uuid4(),
        gate_code="task_completion",
        code="temporary",
        reason="Temporary reason",
        condition={},
        responsible="reviewer",
        valid_from=datetime.now(UTC) - timedelta(minutes=1),
        valid_until=datetime.now(UTC) + timedelta(minutes=1),
        approval_source="external",
        approval_reference="ticket:123",
        approved_by="reviewer",
        approved_at=datetime.now(UTC),
    )

    pending = engine.evaluate(
        gate,
        {},
        [],
        [SdlcException(status=ReviewStatus.PENDING, **base)],
    )
    approved_without_authority = engine.evaluate(
        gate,
        {},
        [],
        [SdlcException(status=ReviewStatus.APPROVED, **base)],
    )

    assert pending.result == EvaluationResult.BLOCK
    assert approved_without_authority.result == EvaluationResult.BLOCK


def test_authorized_exception_can_bypass_only_when_complete() -> None:
    class AllowAuthority:
        def is_authorized(self, exception: SdlcException) -> bool:
            return exception.approval_reference == "ticket:123"

    gate = make_gate("task_completion", ["closure_evidence"])
    exception = SdlcException(
        id=uuid4(),
        workflow_id=uuid4(),
        gate_code="task_completion",
        code="temporary",
        reason="Temporary reason",
        condition={},
        status=ReviewStatus.APPROVED,
        responsible="reviewer",
        valid_from=datetime.now(UTC) - timedelta(minutes=1),
        valid_until=datetime.now(UTC) + timedelta(minutes=1),
        approval_source="external",
        approval_reference="ticket:123",
    )

    decision = WorkflowEngine(approval_authority=AllowAuthority()).evaluate(
        gate, {}, [], [exception]
    )

    assert decision.result == EvaluationResult.PASS
    assert decision.applied_exceptions == ["temporary"]


def test_unknown_workflow_check_is_an_evaluation_error() -> None:
    decision = WorkflowEngine().evaluate(make_gate("custom", ["unknown_check"]), {}, [], [])

    assert decision.result == EvaluationResult.BLOCK
    assert decision.errors == ["Check de workflow no soportado: unknown_check"]
