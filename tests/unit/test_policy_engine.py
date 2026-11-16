from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from sdlc_manager.domain.enums import EvaluationResult
from sdlc_manager.engines.policy_engine import PolicyEngine, PolicyEvaluationError
from sdlc_manager.infrastructure.policy_loader.loader import PolicyLoader, PolicyLoadError


def load_engine() -> PolicyEngine:
    policies = PolicyLoader([Path(__file__).parents[2] / "knowledge" / "rules"]).load()
    return PolicyEngine(policies)


def test_loads_demo_policies() -> None:
    engine = load_engine()
    assert {item.id for item in engine.policies} == {"DEMO-001", "SDLC-002", "SDLC-003"}


def test_invalid_yaml_is_identifiable(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("id: only-id\n", encoding="utf-8")
    with pytest.raises(PolicyLoadError, match="Politica invalida"):
        PolicyLoader([invalid]).load()


def test_extension_rule_is_applicable() -> None:
    rules = load_engine().applicable_rules(
        {"event": "file_change", "changed_files": ["artifacts/sample.artifact"]}
    )
    assert [item.rule.id for item in rules] == ["DEMO-001"]


def test_non_matching_event_is_not_applicable() -> None:
    rules = load_engine().applicable_rules(
        {"event": "file_change", "changed_files": ["queries/report.sql"]}
    )
    assert rules == []


def test_invalid_operator_is_rejected() -> None:
    with pytest.raises(PolicyEvaluationError, match="Operador no permitido"):
        load_engine().evaluate_conditions(
            {"field": "value", "operator": "execute", "value": "x"}, {"value": "x"}
        )


def test_block_changes_to_pass_after_verified_evidence() -> None:
    engine = load_engine()
    context = {"event": "file_change", "changed_files": ["artifacts/sample.artifact"]}
    blocked = engine.evaluate_gate("task_completion", context, {"DEMO-001": set()}, uuid4())
    passed = engine.evaluate_gate(
        "task_completion",
        context,
        {
            "DEMO-001": {
                "baseline_reference",
                "comparison_result",
                "compatibility_check",
            }
        },
        uuid4(),
    )
    assert blocked.result == EvaluationResult.BLOCK
    assert passed.result == EvaluationResult.PASS


def test_performance_rule_returns_warn() -> None:
    decision = load_engine().evaluate_gate(
        "task_completion",
        {"event": "report_change", "component": "reporting"},
        {},
        uuid4(),
    )
    assert decision.result == EvaluationResult.WARN


def test_user_story_preparation_rule_blocks() -> None:
    decision = load_engine().evaluate_gate(
        "development_start",
        {
            "event": "development_start",
            "acceptance_criteria_present": False,
            "dependencies_resolved": False,
        },
        {},
        uuid4(),
    )
    assert decision.result == EvaluationResult.BLOCK
