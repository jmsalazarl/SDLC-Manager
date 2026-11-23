from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from integrations.common.hook_runner import (  # noqa: E402
    build_context_message,
    run_native_event,
)


def format_kiro_output(result: dict[str, Any]) -> str:
    context = build_context_message(result)
    return f"{context}\n" if context else ""


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
