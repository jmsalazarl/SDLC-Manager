from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from integrations.common.event_adapter import (  # noqa: E402
    normalize_file_event,
    project_id_from_environment,
)
from integrations.common.process_event import (  # noqa: E402
    run_normalized_event,
    write_adapter_error,
)


def build_event(payload: dict[str, Any]) -> dict[str, Any]:
    return normalize_file_event(payload, "kiro", project_id_from_environment())


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("El payload del hook debe ser un objeto JSON")
        event = build_event(payload)
    except (json.JSONDecodeError, ValueError) as error:
        sys.stderr.write(f"sdlc-manager kiro adapter: {error}\n")
        return write_adapter_error("INVALID_EVENT", str(error))
    original_stdin = sys.stdin
    try:
        sys.stdin = _JsonInput(event)
        return run_normalized_event("kiro")
    finally:
        sys.stdin = original_stdin


class _JsonInput:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.buffer = _Buffer(json.dumps(payload, ensure_ascii=False).encode("utf-8"))


class _Buffer:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def read(self, size: int = -1) -> bytes:
        return self.payload[:size] if size >= 0 else self.payload


if __name__ == "__main__":
    raise SystemExit(main())
