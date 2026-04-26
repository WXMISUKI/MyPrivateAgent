"""Maintenance helpers for feedback data quality tasks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

from sqlalchemy.orm import Session


FeedbackKey = Tuple[int, Optional[int], int]


@dataclass
class FeedbackDuplicateGroup:
    """Represents one duplicate key group and its keep/delete decision."""

    key: FeedbackKey
    keep: Any
    duplicates: List[Any]
    inherited_learning_id: Optional[str] = None


def _record_sort_key(record: Any) -> Tuple[datetime, int]:
    created_at = getattr(record, "created_at", None)
    if not isinstance(created_at, datetime):
        created_at = datetime.min

    raw_id = getattr(record, "id", 0)
    try:
        normalized_id = int(raw_id)
    except (TypeError, ValueError):
        normalized_id = 0
    return created_at, normalized_id


def build_feedback_dedupe_plan(records: Iterable[Any]) -> List[FeedbackDuplicateGroup]:
    """Build dedupe decisions for records grouped by (conversation_id, message_id, user_id)."""
    grouped: Dict[FeedbackKey, List[Any]] = {}
    for record in records:
        key: FeedbackKey = (
            int(getattr(record, "conversation_id")),
            getattr(record, "message_id"),
            int(getattr(record, "user_id")),
        )
        grouped.setdefault(key, []).append(record)

    plan: List[FeedbackDuplicateGroup] = []
    for key, rows in grouped.items():
        if len(rows) <= 1:
            continue

        sorted_rows = sorted(rows, key=_record_sort_key, reverse=True)
        keep = sorted_rows[0]
        duplicates = sorted_rows[1:]

        inherited_learning_id = None
        keep_learning_id = getattr(keep, "created_learning_id", None)
        if not keep_learning_id:
            for item in duplicates:
                candidate = getattr(item, "created_learning_id", None)
                if candidate:
                    inherited_learning_id = candidate
                    break

        plan.append(
            FeedbackDuplicateGroup(
                key=key,
                keep=keep,
                duplicates=duplicates,
                inherited_learning_id=inherited_learning_id,
            )
        )

    plan.sort(
        key=lambda item: (
            -len(item.duplicates),
            item.key[0],
            -1 if item.key[1] is None else int(item.key[1]),
            item.key[2],
        )
    )
    return plan


def dedupe_message_feedback_records(
    db: Session,
    *,
    dry_run: bool = True,
    include_null_message: bool = False,
    limit_groups: Optional[int] = None,
) -> Dict[str, Any]:
    """Dedupe feedback rows and return an execution summary."""
    try:
        try:
            from models import MessageFeedbackRecord
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.models import MessageFeedbackRecord

        query = db.query(MessageFeedbackRecord).filter(
            MessageFeedbackRecord.user_id.isnot(None),
        )
        if not include_null_message:
            query = query.filter(MessageFeedbackRecord.message_id.isnot(None))

        records = query.all()
        plan = build_feedback_dedupe_plan(records)
        if isinstance(limit_groups, int) and limit_groups > 0:
            plan = plan[:limit_groups]

        rows_to_delete = sum(len(item.duplicates) for item in plan)
        rows_updated = 0
        rows_deleted = 0

        for item in plan:
            if item.inherited_learning_id and not getattr(item.keep, "created_learning_id", None):
                item.keep.created_learning_id = item.inherited_learning_id
                rows_updated += 1

            if dry_run:
                continue

            for duplicate in item.duplicates:
                db.delete(duplicate)
                rows_deleted += 1

        if not dry_run and (rows_deleted > 0 or rows_updated > 0):
            db.commit()

        return {
            "dry_run": dry_run,
            "include_null_message": include_null_message,
            "groups_total": len(plan),
            "rows_to_delete": rows_to_delete,
            "rows_deleted": rows_deleted if not dry_run else 0,
            "rows_updated": rows_updated if not dry_run else 0,
            "groups": [
                {
                    "conversation_id": item.key[0],
                    "message_id": item.key[1],
                    "user_id": item.key[2],
                    "keep_id": getattr(item.keep, "id", None),
                    "delete_ids": [getattr(row, "id", None) for row in item.duplicates],
                    "inherited_learning_id": item.inherited_learning_id,
                }
                for item in plan
            ],
        }
    except Exception:
        if not dry_run:
            db.rollback()
        raise
