import json
import unittest

import httpx

from backend.capability_runtime.clients.http_client import HttpCapabilityClient
from backend.capability_runtime.contracts import CapabilityDefinition
from backend.capability_runtime.provider_consumption_service import ProviderConsumptionService
from backend.capability_runtime.providers.knowledge_http_provider import build_http_knowledge_capabilities
from backend.capability_runtime.providers.voice_provider import build_voice_capabilities
from backend.capability_runtime.registry import CapabilityRegistry
from backend.capability_runtime.service import CapabilityRuntimeService


def _json_response(payload, status_code=200):
    return httpx.Response(
        status_code,
        headers={"content-type": "application/json"},
        content=json.dumps(payload).encode("utf-8"),
    )


class ProviderConsumptionServiceTests(unittest.TestCase):
    def test_local_fallback_provider_reports_disabled_without_external_provider(self):
        service = ProviderConsumptionService(
            CapabilityRuntimeService(CapabilityRegistry(build_voice_capabilities()))
        )

        payload = service.list_providers()

        self.assertEqual(payload["contract_version"], "provider-service-consumption-v1")
        edge = next(provider for provider in payload["providers"] if provider["provider_id"] == "edge_tts")
        self.assertEqual(edge["overall_status"], "disabled")
        self.assertEqual(edge["boundaries"]["default_chat_grounding"], "not_changed")
        self.assertNotIn("api_key", json.dumps(edge).lower())

    def test_knowledge_provider_readiness_preserves_runtime_boundaries(self):
        def handler(request):
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
            raise AssertionError(f"Unexpected path: {request.url.path}")

        client = HttpCapabilityClient(
            base_url="http://knowledge.test",
            transport=httpx.MockTransport(handler),
        )
        runtime = CapabilityRuntimeService(
            CapabilityRegistry(build_http_knowledge_capabilities(base_url="http://knowledge.test", client=client))
        )
        service = ProviderConsumptionService(runtime)

        provider = service.get_provider("unifiedKnowledgeProvider")["provider"]

        self.assertEqual(provider["overall_status"], "ready")
        self.assertEqual(provider["kind"], "knowledge")
        self.assertEqual(provider["base_url"], "http://knowledge.test")
        self.assertIn("knowledge.rag.retrieve", {item["capability_id"] for item in provider["capabilities"]})
        self.assertEqual(provider["boundaries"]["default_chat_grounding"], "disabled")
        self.assertEqual(provider["boundaries"]["graphrag_execution"], "not_promoted")
        self.assertEqual(provider["boundaries"]["source_binding_automation"], "disabled")
        graph_gate = next(gate for gate in provider["gates"] if gate["capability_id"] == "knowledge.graph.query")
        self.assertEqual(graph_gate["status"], "gated")

    def test_evidence_preview_is_compact_and_recommends_caller_side_use(self):
        def handler(request):
            if request.url.path == "/health":
                return _json_response({"status": "ok"})
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
            raise AssertionError(f"Unexpected path: {request.url.path}")

        client = HttpCapabilityClient(
            base_url="http://knowledge.test",
            transport=httpx.MockTransport(handler),
        )
        runtime = CapabilityRuntimeService(
            CapabilityRegistry(build_http_knowledge_capabilities(base_url="http://knowledge.test", client=client))
        )
        service = ProviderConsumptionService(runtime)

        preview = service.preview_evidence("unifiedKnowledgeProvider")["evidence_package"]

        self.assertEqual(preview["readiness"]["overall_status"], "ready")
        self.assertEqual(preview["recommended_action"], "continue_caller_side_governed_explicit_use")
        self.assertIn("real_caller_feedback_trigger", preview["provider_reopen_gate"]["allowed_triggers"])
        serialized = json.dumps(preview).lower()
        self.assertNotIn("api_key", serialized)
        self.assertNotIn("retrieved document", serialized)

    def test_explicit_invoke_delegates_to_capability_runtime(self):
        def handler(request):
            if request.url.path == "/api/rag/retrieve":
                payload = json.loads(request.content.decode("utf-8"))
                self.assertEqual(payload["query"], "公司主营业务是什么？")
                return _json_response(
                    {
                        "ok": True,
                        "result": {
                            "answer_context": "company context",
                            "documents": [
                                {
                                    "source_id": "company_profile",
                                    "document_id": "company-profile-2025",
                                    "title": "Company Profile",
                                    "snippet": "business scope",
                                    "score": 0.9,
                                    "citation": "company-profile-2025#p1",
                                }
                            ],
                        },
                    }
                )
            if request.url.path in {"/health", "/api/catalog"}:
                return _json_response({"status": "ok", "catalog": {"knowledge_bases": [], "graphs": []}})
            raise AssertionError(f"Unexpected path: {request.url.path}")

        client = HttpCapabilityClient(
            base_url="http://knowledge.test",
            transport=httpx.MockTransport(handler),
        )
        runtime = CapabilityRuntimeService(
            CapabilityRegistry(build_http_knowledge_capabilities(base_url="http://knowledge.test", client=client))
        )
        service = ProviderConsumptionService(runtime)

        result = service.invoke_provider_capability(
            "unifiedKnowledgeProvider",
            "knowledge.rag.retrieve",
            {"query": "公司主营业务是什么？"},
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["provider_id"], "unifiedKnowledgeProvider")
        self.assertEqual(result["invocation_boundary"]["explicit_only"], True)
        self.assertEqual(result["invocation_boundary"]["source_binding_automation"], "not_changed")
        self.assertEqual(result["result"]["documents"][0]["citation"], "company-profile-2025#p1")

    def test_invoke_fails_closed_when_provider_does_not_own_capability(self):
        capability = CapabilityDefinition(
            capability_id="custom.echo",
            kind="utility",
            transport="local",
            provider="customProvider",
            title="Echo",
            description="Echo utility",
            invoker=lambda payload: {"ok": True, "result": payload},
        )
        runtime = CapabilityRuntimeService(CapabilityRegistry([capability]))
        service = ProviderConsumptionService(runtime)

        result = service.invoke_provider_capability("customProvider", "knowledge.rag.retrieve", {"query": "x"})

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "SERVICE_PROVIDER_CAPABILITY_NOT_OWNED")
        self.assertEqual(result["error"]["owned_capability_ids"], ["custom.echo"])


if __name__ == "__main__":
    unittest.main()
