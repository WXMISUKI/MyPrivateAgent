"""CLI tool to deduplicate historical message feedback rows."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict


def _bootstrap_imports():
    root = Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    try:
        from database import SessionLocal  # type: ignore
        from services.feedback_maintenance_service import dedupe_message_feedback_records  # type: ignore
    except ModuleNotFoundError:
        from backend.database import SessionLocal  # type: ignore
        from backend.services.feedback_maintenance_service import dedupe_message_feedback_records  # type: ignore
    return SessionLocal, dedupe_message_feedback_records


def _format_summary(summary: Dict[str, Any], *, preview_limit: int = 20) -> str:
    lines = [
        f"mode: {'dry-run' if summary.get('dry_run') else 'apply'}",
        f"groups_total: {summary.get('groups_total', 0)}",
        f"rows_to_delete: {summary.get('rows_to_delete', 0)}",
        f"rows_deleted: {summary.get('rows_deleted', 0)}",
        f"rows_updated: {summary.get('rows_updated', 0)}",
    ]

    groups = list(summary.get("groups", []) or [])
    if groups:
        lines.append("")
        lines.append(f"preview ({min(preview_limit, len(groups))}/{len(groups)} groups):")
        for item in groups[:preview_limit]:
            lines.append(
                "  - conv={conversation_id}, msg={message_id}, user={user_id}, keep={keep_id}, delete={delete_ids}, inherit_learning={inherited_learning_id}".format(
                    **item
                )
            )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deduplicate message_feedback by (conversation_id, message_id, user_id).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply deletion. Default is dry-run preview.",
    )
    parser.add_argument(
        "--include-null-message",
        action="store_true",
        help="Also dedupe groups where message_id is NULL.",
    )
    parser.add_argument(
        "--limit-groups",
        type=int,
        default=0,
        help="Only process first N duplicate groups (0 means all).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON summary.",
    )
    parser.add_argument(
        "--preview-limit",
        type=int,
        default=20,
        help="How many duplicate groups to print in text mode.",
    )

    args = parser.parse_args()
    SessionLocal, dedupe_message_feedback_records = _bootstrap_imports()

    db = SessionLocal()
    try:
        summary = dedupe_message_feedback_records(
            db,
            dry_run=not args.apply,
            include_null_message=args.include_null_message,
            limit_groups=args.limit_groups if args.limit_groups > 0 else None,
        )

        if args.json:
            print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
        else:
            print(_format_summary(summary, preview_limit=max(1, int(args.preview_limit))))

        return 0
    except Exception as exc:  # pragma: no cover - operational safety
        print(f"[dedupe_message_feedback] failed: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
