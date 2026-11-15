import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from integrations.common.process_event import run_normalized_event  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(run_normalized_event("opencode"))
