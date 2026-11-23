from __future__ import annotations

# sdlc-manager-managed
import json
import sys

# El instalador reemplaza esta marca con la raiz de SDLC Manager.
MANAGER_ROOT = "__SDLC_MANAGER_ROOT__"
sys.path.insert(0, MANAGER_ROOT)

from integrations.common.hook_runner import run_native_event  # noqa: E402


def format_codex_output(result: dict[str, object], hook_event_name: str) -> str:
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
        return "{}\n"
    context = "SDLC Manager:\n- " + "\n- ".join(messages)
    if decision in {"WARN", "BLOCK"}:
        context = f"{context}\nDecision: {decision}."
    payload = {
        "hookSpecificOutput": {
            "hookEventName": hook_event_name,
            "additionalContext": context[:10000],
        }
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"


def main() -> int:
    hook_event_name = "UserPromptSubmit"
    if len(sys.argv) > 1 and sys.argv[1] in {
        "PostToolUse",
        "SessionStart",
        "UserPromptSubmit",
    }:
        hook_event_name = sys.argv[1]

    def formatter(result: dict[str, object]) -> str:
        return format_codex_output(result, hook_event_name)

    return run_native_event("codex", formatter)


if __name__ == "__main__":
    raise SystemExit(main())
