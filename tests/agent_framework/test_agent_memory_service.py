import unittest
from pathlib import Path
import shutil
import uuid

from backend.services.agent_memory_service import AgentMemoryService


class AgentMemoryServiceTests(unittest.TestCase):
    def _make_tmp_dir(self) -> Path:
        base = Path(__file__).resolve().parent / ".tmp"
        base.mkdir(exist_ok=True)
        path = base / f"agent_memory_{uuid.uuid4().hex}"
        path.mkdir()
        return path

    def test_build_context_loads_existing_layers(self):
        base = self._make_tmp_dir()
        try:
            (base / "GLOBAL_AGENT.md").write_text("global rule", encoding="utf-8")
            (base / "PROJECT_AGENT.md").write_text("project rule", encoding="utf-8")

            service = AgentMemoryService(base)
            context = service.build_context()

            self.assertFalse(context.is_empty)
            self.assertEqual([item.name for item in context.loaded_layers], ["global", "project"])
            self.assertEqual([item.memory_id for item in context.memory_entries], ["memory:global", "memory:project"])
            self.assertEqual(context.memory_entries[0].retrieval_reason, "loaded_layer:global")
            self.assertIn("global rule", context.system_prompt)
            self.assertIn("project rule", context.system_prompt)
            self.assertIn("local", [item.name for item in context.missing_layers])
        finally:
            shutil.rmtree(base, ignore_errors=True)

    def test_build_runtime_contract_reports_layer_state(self):
        base = self._make_tmp_dir()
        try:
            (base / "GLOBAL_AGENT.md").write_text("global rule", encoding="utf-8")

            service = AgentMemoryService(base)
            contract = service.build_runtime_contract()

            self.assertTrue(contract["active"])
            self.assertEqual(contract["contract_version"], "phase-b-memory-entry-v1")
            self.assertEqual(contract["loaded_layers"][0]["name"], "global")
            self.assertEqual(contract["memory_entries"][0]["memory_id"], "memory:global")
            self.assertEqual(contract["memory_entries"][0]["source"], "agent_memory_layer")
            self.assertEqual(contract["memory_entries"][0]["confidence"], 1.0)
            self.assertEqual(contract["memory_entries"][0]["retrieval_reason"], "loaded_layer:global")
            self.assertIn("project", [item["name"] for item in contract["missing_layers"]])
        finally:
            shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
