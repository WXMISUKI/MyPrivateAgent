import unittest
from datetime import datetime
from types import SimpleNamespace

from backend.services.memoryops_contract_service import MemoryOpsContractService


class MemoryOpsContractServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = MemoryOpsContractService()

    def test_instruction_memory_entries_are_normalized(self):
        registry = self.service.build_registry(
            agent_memory_contract={
                "memory_entries": [
                    {
                        "memory_id": "memory:global",
                        "source": "agent_memory_layer",
                        "scope": "global",
                        "content": "global rule",
                        "confidence": 1.0,
                        "retrieval_reason": "loaded_layer:global",
                    }
                ]
            }
        )

        self.assertEqual(registry["entry_count"], 1)
        entry = registry["entries"][0]
        self.assertEqual(entry["kind"], "runtime_instruction_memory")
        self.assertEqual(entry["status"], "active")
        self.assertEqual(entry["ttl_policy"], "none")
        self.assertEqual(entry["injection_trace"]["mode"], "existing_runtime_path")
        self.assertFalse(entry["injection_trace"]["behavior_changed"])

    def test_conversation_summary_maps_to_memoryops_entry(self):
        summary = SimpleNamespace(
            id=7,
            conversation_id=42,
            summary="已压缩 12 条消息。",
            message_count=12,
            last_message_id=99,
            trigger="manual",
            created_at=datetime(2026, 6, 5, 12, 0, 0),
        )

        registry = self.service.build_registry(conversation_summary=summary, conversation_id=42)

        self.assertEqual(registry["entry_count"], 1)
        self.assertTrue(registry["posture"]["conversation_summary"]["available"])
        entry = registry["entries"][0]
        self.assertEqual(entry["kind"], "conversation_summary")
        self.assertEqual(entry["message_count"], 12)
        self.assertEqual(entry["last_message_id"], 99)
        self.assertEqual(entry["audit_source"], "messages")

    def test_absent_summary_is_reported_without_inventing_entry(self):
        registry = self.service.build_registry(conversation_summary=None, conversation_id=42)

        self.assertEqual(registry["entry_count"], 0)
        self.assertFalse(registry["posture"]["conversation_summary"]["available"])
        self.assertEqual(registry["conversation_id"], 42)

    def test_retrieved_knowledge_posture_is_explicit_only(self):
        registry = self.service.build_registry()
        posture = registry["posture"]["retrieved_knowledge_evidence"]

        self.assertTrue(posture["available"])
        self.assertEqual(posture["promotion_mode"], "explicit_only")
        self.assertFalse(posture["stored_as_memory_by_default"])
        self.assertFalse(registry["behavior_boundary"]["retrieval_behavior_changed"])

    def test_registry_is_visibility_only(self):
        registry = self.service.build_registry()

        self.assertEqual(registry["behavior_boundary"]["mode"], "visibility_only")
        self.assertFalse(registry["behavior_boundary"]["chat_context_packing_changed"])
        self.assertFalse(registry["behavior_boundary"]["prompt_injection_changed"])


if __name__ == "__main__":
    unittest.main()
