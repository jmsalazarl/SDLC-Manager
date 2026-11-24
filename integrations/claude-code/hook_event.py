from __future__ import annotations

# sdlc-manager-managed
import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from integrations.common.hook_runner import (  # noqa: E402
    build_context_message,
    run_native_event,
)


def format_claude_output(result: dict[str, Any], hook_event_name: str = "PostToolUse") -> str:
    context = build_context_message(result) or "SDLC Manager: sin recomendaciones aplicables."
    payload = {
        "hookSpecificOutput": {
            "hookEventName": hook_event_name,
            "additionalContext": context[:10000],
        }
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="claude-code")
    parser.add_argument("--format", choices=("raw", "claude"), default="claude")
    parser.add_argument(
        "--event",
        choices=("PostToolUse", "SessionStart", "UserPromptSubmit"),
        default="PostToolUse",
    )
    args = parser.parse_args()
    formatter = (
        (lambda result: format_claude_output(result, args.event))
        if args.format == "claude"
        else None
    )
    return run_native_event(args.source, formatter)


if __name__ == "__main__":
    raise SystemExit(main())
