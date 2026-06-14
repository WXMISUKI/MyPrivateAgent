import json
import unittest
from unittest.mock import patch

import httpx

from backend.capability_runtime.clients.http_client import HttpCapabilityClient
from backend.capability_runtime.provider_onboarding_acceptance_gate import ProviderOnboardingAcceptanceGate
from backend.capability_runtime.provider_consumption_service import ProviderConsumptionService
from backend.capability_runtime.providers.knowledge_http_provider import build_http_knowledge_capabilities
from backend.capability_runtime.registry import CapabilityRegistry
from backend.capability_runtime.service import CapabilityRuntimeService


def _json_response(payload, status_code=200):
    return httpx.Response(
        status_code,
        headers={"content-type": "application/json"},
        content=json.dumps(payload).encode("utf-8"),
    )


def _ready_knowledge_runtime():
    requested_paths = []

    def handler(request):
        requested_paths.append(request.url.path)
        if request.url.path == "/health":
            return _json_response({"status": "ok", "service": "unifiedKnowledgeProvider"})
        if request.url.path == "/api/catalog":
            return _json_response(
                {
                    "status": "ready",
                    "catalog": {
                        "knowledge_bases": [{"id": "company_profile", "status": "ready"}],
                        "graphs": [],
                    },
                }
            )
        raise AssertionError(f"Unexpected provider call: {request.url.path}")

    client = HttpCapabilityClient(
        base_url="http://knowledge.test",
        transport=httpx.MockTransport(handler),
    )
    runtime = CapabilityRuntimeService(
        CapabilityRegistry(build_http_knowledge_capabilities(base_url="http://knowledge.test", client=client))
    )
    return runtime, requested_paths


class ProviderOnboardingAcceptanceGateTests(unittest.TestCase):
    def test_accepts_configured_registered_provider_for_explicit_use(self):
        runtime, requested_paths = _ready_knowledge_runtime()
        gate = ProviderOnboardingAcceptanceGate(
            provider_consumption=ProviderConsumptionService(runtime)
        )

        with patch("backend.config.ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER", True), patch(
            "backend.config.KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL",
            "http://knowledge.test",
        ):
            payload = gate.evaluate_onboarding("knowledge-rag-provider")

        self.assertEqual(payload["contract_version"], "provider-onboarding-acceptance-gate-v1")
        self.assertEqual(payload["decision"], "accepted")
        self.assertEqual(payload["decision_scope"], "explicit_managed_provider_consumption_only")
        self.assertEqual(payload["provider_identity"]["provider_id"], "unifiedKnowledgeProvider")
        self.assertEqual(payload["onboarding"]["configuration_status"], "configured")
        self.assertIn("knowledge.rag.retrieve", payload["owned_capability_ids"])
        self.assertEqual(payload["side_effects"]["provider_invocation"], "not_performed")
        self.assertEqual(payload["boundaries"]["source_binding_automation"], "disabled")
        self.assertNotIn("/api/rag/retrieve", requested_paths)

    def test_resolves_provider_id_to_onboarding_entry(self):
        runtime, _ = _ready_knowledge_runtime()
        gate = ProviderOnboardingAcceptanceGate(
            provider_consumption=ProviderConsumptionService(runtime)
        )

        with patch("backend.config.ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER", True), patch(
            "backend.config.KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL",
            "http://knowledge.test",
        ):
            payload = gate.evaluate_provider("unifiedKnowledgeProvider")

        self.assertEqual(payload["decision"], "accepted")
        self.assertEqual(payload["provider_identity"]["onboarding_id"], "knowledge-rag-provider")

    def test_blocks_unconfigured_provider_without_live_registration(self):
        gate = ProviderOnboardingAcceptanceGate()

        with patch("backend.config.ENABLE_VLM_CAPABILITY_PROVIDER", False), patch(
            "backend.config.VLM_CAPABILITY_PROVIDER_BASE_URL",
            "",
        ):
            payload = gate.evaluate_onboarding("document-vlm-provider")

        self.assertEqual(payload["decision"], "blocked")
        blocker_codes = {blocker["code"] for blocker in payload["blockers"]}
        self.assertIn("ONBOARDING_CONFIGURATION_INCOMPLETE", blocker_codes)
        self.assertIn("SERVICE_PROVIDER_NOT_REGISTERED", blocker_codes)

    def test_unknown_provider_fails_closed(self):
        payload = ProviderOnboardingAcceptanceGate().evaluate_provider("missingProvider")

        self.assertEqual(payload["decision"], "blocked")
        self.assertEqual(payload["blockers"][0]["code"], "PROVIDER_ONBOARDING_NOT_FOUND")

    def test_evidence_excludes_unsafe_payloads(self):
        runtime, _ = _ready_knowledge_runtime()
        gate = ProviderOnboardingAcceptanceGate(
            provider_consumption=ProviderConsumptionService(runtime)
        )

        with patch("backend.config.ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER", True), patch(
            "backend.config.KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL",
            "http://knowledge.test",
        ):
            payload = gate.evaluate_onboarding("knowledge-rag-provider")

        serialized = json.dumps(payload).lower()
        self.assertNotIn("api_key", serialized)
        self.assertNotIn("secret_value", serialized)
        self.assertNotIn("retrieved document", serialized)
        self.assertNotIn("generated answer", serialized)
        self.assertNotIn("callable", serialized)
        self.assertNotIn("client", serialized)


if __name__ == "__main__":
    unittest.main()
