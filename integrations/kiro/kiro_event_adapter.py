from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from integrations.common.hook_runner import run_native_event  # noqa: E402


def format_kiro_output(result: dict[str, Any]) -> str:
    recommendations = result.get("recommendations")
    messages = (
        [item for item in recommendations if isinstance(item, str)]
        if isinstance(recommendations, list)
        else []
    )
    decision = result.get("decision")
    explanation = result.get("explanation")
    if not messages and decision in {"WARN", "BLOCK"} and isinstance(explanation, str):
        messages.append(explanation)
    if (
        not messages
        and result.get("status") in {"rejected", "unsupported", "error"}
        and isinstance(explanation, str)
    ):
        messages.append(explanation)
    if not messages:
        return ""
    context = "SDLC Manager:\n- " + "\n- ".join(messages)
    if decision in {"WARN", "BLOCK"}:
        context = f"{context}\nDecision: {decision}."
    return context[:10000] + "\n"


def format_kiro_exit_code(code: int) -> int:
    """Mantiene visible el contexto de un hook PostFileSave no bloqueante."""
    if code in {0, 10, 20, 30}:
        return 0
    return code


def main() -> int:
    return run_native_event(
        "kiro",
        format_kiro_output,
        default_event_type="file_changed",
        require_affected_files=True,
        exit_code_formatter=format_kiro_exit_code,
    )


if __name__ == "__main__":
    raise SystemExit(main())
