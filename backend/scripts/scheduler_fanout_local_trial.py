"""CLI for deterministic scheduler fan-out local trial."""

from __future__ import annotations

import argparse
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
    from services.scheduler_fanout_local_trial_service import (
        DEFAULT_CHILD_ROLES,
        DEFAULT_ITEM_DETAILS,
        DEFAULT_ITEM_TITLE,
        DEFAULT_MODE,
        DEFAULT_OBJECTIVE,
        SchedulerFanoutLocalTrialService,
    )
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.scheduler_fanout_local_trial_service import (
        DEFAULT_CHILD_ROLES,
        DEFAULT_ITEM_DETAILS,
        DEFAULT_ITEM_TITLE,
        DEFAULT_MODE,
        DEFAULT_OBJECTIVE,
        SchedulerFanoutLocalTrialService,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a deterministic local scheduler fan-out / collect / merge trial.",
    )
    parser.add_argument(
        "--mode",
        choices=["success", "partial-failure", "partial_failure", "blocked"],
        default=DEFAULT_MODE,
        help="Trial mode.",
    )
    parser.add_argument("--objective", default=DEFAULT_OBJECTIVE, help="Local plan objective.")
    parser.add_argument("--item-title", default=DEFAULT_ITEM_TITLE, help="Local plan item title.")
    parser.add_argument("--item-details", default=DEFAULT_ITEM_DETAILS, help="Local plan item details.")
    parser.add_argument(
        "--child-roles",
        default=",".join(DEFAULT_CHILD_ROLES),
        help="Comma-separated child roles for the local trial.",
    )
    parser.add_argument("--failed-role", default="frontend", help="Role to fail in partial-failure mode.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    roles = [role.strip() for role in str(args.child_roles or "").split(",") if role.strip()]
    report = SchedulerFanoutLocalTrialService().run_trial(
        mode=args.mode,
        objective=args.objective,
        item_title=args.item_title,
        item_details=args.item_details,
        child_roles=roles,
        failed_role=args.failed_role,
    )
    payload = report.to_dict()
    print(json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty else None))
    if report.decision == "go":
        return 0
    if report.decision == "review":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
