"""Generate Embedded SDK recovery acceptance smoke evidence."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    from backend.agent_framework.recovery_acceptance_smoke import (  # noqa: E402
        run_embedded_sdk_recovery_acceptance_smoke,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario",
        choices=["accepted", "memory-only", "missing-registry-binding"],
        default="accepted",
        help="Controlled acceptance scenario to run.",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON evidence.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        payload = run_embedded_sdk_recovery_acceptance_smoke(args.scenario)
    print(json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0 if payload.get("decision") == "accepted" else 2


if __name__ == "__main__":
    raise SystemExit(main())
