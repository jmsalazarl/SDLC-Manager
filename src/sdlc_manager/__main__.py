from __future__ import annotations

import sys
from collections.abc import Sequence

from .cli import run_cli
from .config import get_settings
from .infrastructure.database.migrations import run_migrations
from .mcp.server import create_server
from .mcp.server import main as run_server


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments:
        return run_cli(arguments, sys.stdin.buffer, sys.stdout, sys.stderr)

    settings = get_settings()
    if settings.auto_migrate:
        run_migrations(settings)
    run_server(create_server(settings, initialize_schema=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
