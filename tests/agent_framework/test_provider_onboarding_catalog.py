import json
import unittest
from unittest.mock import patch

from backend.capability_runtime.provider_onboarding_catalog import ProviderOnboardingCatalogService
from backend.capability_runtime.provider_consumption_service import ProviderConsumptionService
from backend.capability_runtime.providers.knowledge_http_provider import build_http_knowledge_capabilities
from backend.capability_runtime.registry import CapabilityRegistry
from backend.capability_runtime.service import CapabilityRuntimeService


class ProviderOnboardingCatalogTests(unittest.TestCase):
    def test_catalog_lists_known_external_provider_families(self):
        payload = ProviderOnboardingCatalogService().list_entries()

        self.assertEqual(payload["contract_version"], "provider-onboarding-catalog-v1")
        entries = {entry["onboarding_id"]: entry for entry in payload["entries"]}
        self.assertEqual(
            set(entries),
            {
                "knowledge-rag-provider",
                "voice-asr-tts-provider",
                "document-ocr-provider",
                "document-layout-provider",
                "document-vlm-provider",
            },
        )
        self.assertIn("knowledge.rag.retrieve", entries["knowledge-rag-provider"]["capability_ids"])
        self.assertIn("voice.asr.vosk", entries["voice-asr-tts-provider"]["capability_ids"])
        self.assertIn("document.ocr.extract", entries["document-ocr-provider"]["capability_ids"])
        self.assertIn("document.layout.parse", entries["document-layout-provider"]["capability_ids"])
        self.assertIn("document.vlm.parse.async", entries["document-vlm-provider"]["capability_ids"])

    def test_catalog_payload_is_secret_free(self):
        payload = ProviderOnboardingCatalogService().get_entry("knowledge-rag-provider")

        serialized = json.dumps(payload).lower()
        self.assertNotIn("api_key", serialized)
        self.assertNotIn("secret_value", serialized)
        self.assertNotIn("token_value", serialized)
        self.assertNotIn("retrieved documents", serialized)
        self.assertNotIn("generated answers", serialized)

    def test_readiness_reports_configured_without_live_probe(self):
        with patch("backend.config.ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER", True), patch(
            "backend.config.KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL",
            "http://127.0.0.1:8020",
        ):
            readiness = ProviderOnboardingCatalogService().get_readiness("knowledge-rag-provider")

        self.assertEqual(readiness["configuration_status"], "configured")
        self.assertEqual(readiness["recommended_action"], "run_live_service_provider_probe")
        runtime_probe = next(check for check in readiness["checks"] if check["id"] == "runtime_probe")
        self.assertEqual(runtime_probe["status"], "probe_required")
        self.assertEqual(readiness["boundaries"]["default_chat_grounding"], "disabled")

    def test_readiness_reports_missing_env_without_mutation(self):
        with patch("backend.config.ENABLE_VLM_CAPABILITY_PROVIDER", False), patch(
            "backend.config.VLM_CAPABILITY_PROVIDER_BASE_URL",
            "",
        ):
            readiness = ProviderOnboardingCatalogService().get_readiness("document-vlm-provider")

        self.assertEqual(readiness["configuration_status"], "unconfigured")
        self.assertEqual(readiness["recommended_action"], "configure_required_provider_environment")
        missing = {check["id"] for check in readiness["checks"] if check["status"] == "missing"}
        self.assertEqual(missing, {"enable_flag", "base_url"})

    def test_service_provider_entry_references_onboarding_catalog(self):
        runtime = CapabilityRuntimeService(
            CapabilityRegistry(build_http_knowledge_capabilities(base_url="http://knowledge.test"))
        )
        service = ProviderConsumptionService(runtime)

        provider = service.list_providers()["providers"][0]

        self.assertEqual(provider["provider_id"], "unifiedKnowledgeProvider")
        self.assertEqual(provider["onboarding_id"], "knowledge-rag-provider")
        self.assertEqual(provider["onboarding_path"], "/api/provider-onboarding/knowledge-rag-provider")


if __name__ == "__main__":
    unittest.main()
