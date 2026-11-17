from __future__ import annotations

# sdlc-manager-managed
import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from integrations.common.hook_runner import run_native_event  # noqa: E402


def format_claude_output(result: dict[str, Any]) -> str:
    decision = result.get("decision")
    explanation = result.get("explanation") or ""
    practices = result.get("applicable_practices") or []
    experiences = result.get("relevant_experiences") or []
    guidance = [f"SDLC Manager: {explanation}"]
    if decision:
        guidance.append(f"Decision: {decision}.")
    if practices:
        guidance.append(f"Practicas aplicables: {len(practices)}.")
    if experiences:
        guidance.append(f"Experiencias relevantes: {len(experiences)}.")
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": " ".join(guidance)[:10000],
        }
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="claude-code")
    parser.add_argument("--format", choices=("raw", "claude"), default="claude")
    args = parser.parse_args()
    formatter = format_claude_output if args.format == "claude" else None
    return run_native_event(args.source, formatter)


if __name__ == "__main__":
    raise SystemExit(main())
