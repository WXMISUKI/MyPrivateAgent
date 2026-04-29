import unittest

from backend.database import Base, engine, SessionLocal
from backend.services.remediation_status_service import RemediationStatusService


class RemediationStatusServiceTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_upsert_and_list_status(self):
        service = RemediationStatusService(self.db)
        updated = service.upsert_status(
            action_id="fix_final_synthesis_chain",
            status="in_progress",
            owner="agent-core",
            module="completion_synthesis",
            note="正在修复",
            updated_by="tester",
        )
        self.assertEqual(updated["action_id"], "fix_final_synthesis_chain")
        self.assertEqual(updated["status"], "in_progress")

        items = service.list_statuses()
        self.assertTrue(any(item["action_id"] == "fix_final_synthesis_chain" for item in items))
        status_map = service.status_map()
        self.assertEqual(status_map["fix_final_synthesis_chain"]["owner"], "agent-core")

    def test_invalid_status_raises(self):
        service = RemediationStatusService(self.db)
        with self.assertRaises(ValueError):
            service.upsert_status(action_id="fix_final_synthesis_chain", status="invalid")


if __name__ == "__main__":
    unittest.main()
