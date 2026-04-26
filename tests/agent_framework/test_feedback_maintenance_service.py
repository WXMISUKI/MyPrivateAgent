from datetime import datetime, timedelta
from types import SimpleNamespace
import unittest

from backend.services.feedback_maintenance_service import (
    build_feedback_dedupe_plan,
    dedupe_message_feedback_records,
)


class _FakeQuery:
    def __init__(self, records):
        self._records = records

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return list(self._records)


class _FakeDb:
    def __init__(self, records):
        self._records = records
        self.deleted = []
        self.commits = 0
        self.rollbacks = 0

    def query(self, *args, **kwargs):
        return _FakeQuery(self._records)

    def delete(self, row):
        self.deleted.append(row)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class FeedbackMaintenanceServiceTests(unittest.TestCase):
    def test_build_feedback_dedupe_plan_keeps_latest_record(self):
        base_time = datetime(2026, 4, 24, 12, 0, 0)
        older = SimpleNamespace(
            id=1,
            conversation_id=7,
            message_id=88,
            user_id=3,
            created_at=base_time,
            created_learning_id=None,
        )
        newer = SimpleNamespace(
            id=2,
            conversation_id=7,
            message_id=88,
            user_id=3,
            created_at=base_time + timedelta(seconds=1),
            created_learning_id=None,
        )

        plan = build_feedback_dedupe_plan([older, newer])
        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0].keep.id, 2)
        self.assertEqual([row.id for row in plan[0].duplicates], [1])

    def test_build_feedback_dedupe_plan_inherits_learning_id_when_needed(self):
        base_time = datetime(2026, 4, 24, 12, 0, 0)
        newest_without_learning = SimpleNamespace(
            id=10,
            conversation_id=9,
            message_id=66,
            user_id=5,
            created_at=base_time + timedelta(seconds=2),
            created_learning_id=None,
        )
        older_with_learning = SimpleNamespace(
            id=9,
            conversation_id=9,
            message_id=66,
            user_id=5,
            created_at=base_time,
            created_learning_id="LRN-20260424-XYZ",
        )

        plan = build_feedback_dedupe_plan([newest_without_learning, older_with_learning])
        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0].inherited_learning_id, "LRN-20260424-XYZ")

    def test_dedupe_message_feedback_records_apply_deletes_duplicates(self):
        base_time = datetime(2026, 4, 24, 12, 0, 0)
        keep = SimpleNamespace(
            id=22,
            conversation_id=11,
            message_id=77,
            user_id=2,
            created_at=base_time + timedelta(seconds=1),
            created_learning_id=None,
        )
        duplicate = SimpleNamespace(
            id=21,
            conversation_id=11,
            message_id=77,
            user_id=2,
            created_at=base_time,
            created_learning_id="LRN-20260424-AAA",
        )
        unrelated = SimpleNamespace(
            id=30,
            conversation_id=11,
            message_id=78,
            user_id=2,
            created_at=base_time,
            created_learning_id=None,
        )
        db = _FakeDb([keep, duplicate, unrelated])

        summary = dedupe_message_feedback_records(db, dry_run=False)

        self.assertEqual(summary["groups_total"], 1)
        self.assertEqual(summary["rows_to_delete"], 1)
        self.assertEqual(summary["rows_deleted"], 1)
        self.assertEqual(summary["rows_updated"], 1)
        self.assertEqual(keep.created_learning_id, "LRN-20260424-AAA")
        self.assertEqual(len(db.deleted), 1)
        self.assertEqual(db.deleted[0].id, 21)
        self.assertEqual(db.commits, 1)
        self.assertEqual(db.rollbacks, 0)


if __name__ == "__main__":
    unittest.main()
