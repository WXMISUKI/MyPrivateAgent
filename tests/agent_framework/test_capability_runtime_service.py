import unittest
from unittest.mock import patch

from backend.capability_runtime.providers.voice_provider import build_voice_capabilities
from backend.capability_runtime.registry import CapabilityRegistry, get_default_capability_registry
from backend.capability_runtime.service import CapabilityRuntimeService
from backend.voice_runtime.service import VoiceRuntimeSettings


class CapabilityRuntimeServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = CapabilityRuntimeService(CapabilityRegistry(build_voice_capabilities()))

    def test_registry_lists_voice_capabilities(self):
        payload = self.service.list_capabilities()

        capability_ids = {item["capability_id"] for item in payload["capabilities"]}
        self.assertEqual(payload["contract_version"], "capability-runtime-v1")
        self.assertIn("voice.tts.edge", capability_ids)
        self.assertIn("voice.asr.vosk", capability_ids)

        tts = next(item for item in payload["capabilities"] if item["capability_id"] == "voice.tts.edge")
        self.assertEqual(tts["kind"], "tts")
        self.assertEqual(tts["transport"], "local")
        self.assertEqual(tts["provider"], "edge_tts")
        self.assertEqual(tts["metadata"]["runtime_role"], "legacy_local_fallback")
        self.assertEqual(tts["metadata"]["recommended_provider"], "unifiedTTSandASR")
        self.assertIn("status", tts)
        self.assertIn("input_schema", tts)
        self.assertIn("output_schema", tts)

    def test_get_capability_returns_provider_neutral_contract(self):
        capability = self.service.get_capability("voice.asr.vosk")

        self.assertEqual(capability["capability_id"], "voice.asr.vosk")
        self.assertEqual(capability["kind"], "asr")
        self.assertEqual(capability["provider"], "vosk_server")
        self.assertNotIn("settings", capability)

    def test_health_reuses_registry_status_and_reason(self):
        health = self.service.get_capability_health("voice.tts.edge")

        self.assertEqual(health["capability_id"], "voice.tts.edge")
        self.assertIn(health["status"], {"disabled", "ready", "missing_dependency", "unconfigured", "unsupported"})
        if health["status"] != "ready":
            self.assertTrue(health["reason"])

    def test_unknown_capability_raises_lookup_error(self):
        with self.assertRaises(LookupError):
            self.service.get_capability("unknown")

    def test_disabled_voice_invocation_returns_structured_error(self):
        with patch(
            "backend.voice_runtime.service.VoiceRuntimeSettings.from_config",
            return_value=VoiceRuntimeSettings(enabled=False),
        ):
            result = self.service.invoke("voice.tts.edge", {"text": "hello"})

        self.assertFalse(result["ok"])
        self.assertEqual(result["capability_id"], "voice.tts.edge")
        self.assertEqual(result["error"]["code"], "VOICE_RUNTIME_DISABLED")

    def test_default_registry_omits_knowledge_capabilities_when_unconfigured(self):
        with patch("backend.config.ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER", False):
            registry = get_default_capability_registry()

        capability_ids = {capability.capability_id for capability in registry.list()}

        self.assertNotIn("knowledge.rag.retrieve", capability_ids)
        self.assertNotIn("knowledge.graph.query", capability_ids)

    def test_default_registry_adds_knowledge_capabilities_when_configured(self):
        with patch("backend.config.ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER", True), patch(
            "backend.config.KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL",
            "http://knowledge.test",
        ):
            registry = get_default_capability_registry()

        capability_ids = {capability.capability_id for capability in registry.list()}

        self.assertIn("knowledge.rag.retrieve", capability_ids)
        self.assertIn("knowledge.graph.query", capability_ids)


if __name__ == "__main__":
    unittest.main()
