import unittest
from types import SimpleNamespace

from backend.services.scheduler_runtime_repository import SchedulerRuntimeMetadataRepository


class SchedulerRuntimeMetadataRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.repository = SchedulerRuntimeMetadataRepository()
        self.item = SimpleNamespace(
            item_metadata={
                "required_capabilities": ["filesystem.read"],
                "child_roles": ["backend", "frontend"],
            }
        )

    def test_save_and_find_child_group_entry(self):
        self.repository.save_child_group(
            self.item,
            {
                "run_id": "sched-p1-i2",
                "children": [
                    {
                        "child_execution_id": "backend-child-p1-i2-c1",
                        "agent_role": "backend",
                        "status": "queued",
                    }
                ],
            },
        )

        group, child = self.repository.find_child_group_entry(self.item, "backend-child-p1-i2-c1")

        self.assertIsNotNone(group)
        self.assertIsNotNone(child)
        self.assertEqual(group["run_id"], "sched-p1-i2")
        self.assertEqual(child["agent_role"], "backend")

    def test_append_audit_trail_and_run_trace_keep_recent_entries(self):
        for index in range(55):
            self.repository.append_audit_trail(self.item, {"event_type": f"audit-{index}"}, limit=50)
        for index in range(105):
            self.repository.append_run_trace(self.item, {"event_type": f"trace-{index}"}, limit=100)

        audit_trail = self.repository.get_audit_trail(self.item)
        run_trace = self.repository.get_run_trace(self.item)

        self.assertEqual(len(audit_trail), 50)
        self.assertEqual(audit_trail[0]["event_type"], "audit-5")
        self.assertEqual(len(run_trace), 100)
        self.assertEqual(run_trace[0]["event_type"], "trace-5")

    def test_get_required_capabilities_and_child_roles(self):
        self.assertEqual(self.repository.get_required_capabilities(self.item), ["filesystem.read"])
        self.assertEqual(self.repository.get_child_roles(self.item), ["backend", "frontend"])


if __name__ == "__main__":
    unittest.main()
