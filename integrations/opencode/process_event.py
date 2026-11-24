import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from integrations.common.hook_runner import run_native_event  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(run_native_event("opencode"))
