from __future__ import annotations

from uuid import UUID

import pytest
from pydantic import BaseModel, ValidationError

from sdlc_manager.application.schemas import (
    AnalyzeStoryInput,
    ApplicableRulesInput,
    CreateSprintInput,
    CreateStoryInput,
    EvaluateGateInput,
    RegisterEvidenceInput,
    StartSprintInput,
    VerifyEvidenceInput,
)

PROJECT_ID = "00e57f27-4f4c-47d0-be96-84f1b7162a99"
STORY_ID = "10e57f27-4f4c-47d0-be96-84f1b7162a99"


@pytest.mark.parametrize(
    ("model", "payload", "fields"),
    [
        (CreateSprintInput, {"project_id": PROJECT_ID, "name": "Sprint 1"}, ["project_id"]),
        (
            CreateStoryInput,
            {"project_id": PROJECT_ID, "sprint_id": STORY_ID, "title": "Historia"},
            ["project_id", "sprint_id"],
        ),
        (
            ApplicableRulesInput,
            {"project_id": PROJECT_ID, "event": "file_change", "stage": "implementation"},
            ["project_id"],
        ),
        (
            EvaluateGateInput,
            {"project_id": PROJECT_ID, "user_story_id": STORY_ID, "gate": "task_completion"},
            ["project_id", "user_story_id"],
        ),
        (
            RegisterEvidenceInput,
            {
                "project_id": PROJECT_ID,
                "user_story_id": STORY_ID,
                "policy_id": "SDLC-001",
                "evidence_type": "comparison_result",
                "reference": "evidence://comparison/1",
            },
            ["project_id", "user_story_id"],
        ),
        (
            VerifyEvidenceInput,
            {"project_id": PROJECT_ID, "evidence_id": STORY_ID, "verified_by": "reviewer"},
            ["project_id", "evidence_id"],
        ),
        (
            AnalyzeStoryInput,
            {"project_id": PROJECT_ID, "user_story_id": STORY_ID},
            ["project_id", "user_story_id"],
        ),
        (
            StartSprintInput,
            {"project_id": PROJECT_ID, "sprint_id": STORY_ID},
            ["project_id", "sprint_id"],
        ),
    ],
)
def test_uuid_strings_are_converted_at_mcp_input_boundary(
    model: type[BaseModel], payload: dict[str, object], fields: list[str]
) -> None:
    parsed = model.model_validate(payload)

    for field in fields:
        assert isinstance(getattr(parsed, field), UUID)


@pytest.mark.parametrize("value", ["", "not-a-uuid", "00000000-0000-0000-0000-00000000000"])
def test_invalid_uuid_strings_are_rejected(value: str) -> None:
    with pytest.raises(ValidationError):
        ApplicableRulesInput.model_validate(
            {"project_id": value, "event": "file_change", "stage": "implementation"}
        )


def test_non_string_uuid_values_are_rejected() -> None:
    with pytest.raises(ValidationError):
        ApplicableRulesInput.model_validate(
            {"project_id": 123, "event": "file_change", "stage": "implementation"}
        )
