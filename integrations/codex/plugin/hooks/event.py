from __future__ import annotations

# sdlc-manager-managed
import json
import os
import subprocess
import sys

# El instalador reemplaza esta marca con la raiz de SDLC Manager.
MANAGER_ROOT = "__SDLC_MANAGER_ROOT__"


def main() -> int:
    event_type = sys.argv[1] if len(sys.argv) > 1 else "session_started"
    raw = sys.stdin.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        print("SDLC Manager: evento demasiado grande", file=sys.stderr)
        return 2
    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError:
        print("SDLC Manager: evento invalido", file=sys.stderr)
        return 2
    if not isinstance(payload, dict):
        print("SDLC Manager: evento invalido", file=sys.stderr)
        return 2
    payload["event_type"] = event_type
    payload["source_client"] = "codex"
    command = os.environ.get(
        "SDLC_MANAGER_COMMAND",
        f"uv --directory {MANAGER_ROOT} run --frozen sdlc-manager",
    ).split()
    result = subprocess.run(
        [*command, "event", "process", "--stdin"],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    print(result.stdout, end="")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
