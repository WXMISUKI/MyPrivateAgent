"""CLI startup diagnostics for local demo stability."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _bootstrap_path() -> None:
    root = Path(__file__).resolve().parents[2]
    candidate = str(root)
    if candidate not in sys.path:
        sys.path.insert(0, candidate)


_bootstrap_path()

try:
    from services.startup_diagnostics_service import get_startup_diagnostics_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.startup_diagnostics_service import get_startup_diagnostics_service


def main() -> int:
    report = get_startup_diagnostics_service().collect_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("status") != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
