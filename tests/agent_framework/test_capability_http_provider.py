import json
import unittest

import httpx

from backend.capability_runtime.clients.http_client import HttpCapabilityClient
from backend.capability_runtime.providers.document_vlm_http_provider import build_http_document_vlm_capabilities
from backend.capability_runtime.providers.knowledge_http_provider import build_http_knowledge_capabilities
from backend.capability_runtime.providers.paddleocr_layout_http_provider import build_http_layout_capabilities
from backend.capability_runtime.providers.paddleocr_http_provider import build_http_paddleocr_capabilities
from backend.capability_runtime.providers.voice_http_provider import build_http_voice_capabilities
from backend.capability_runtime.registry import CapabilityRegistry
from backend.capability_runtime.service import CapabilityRuntimeService


def _json_response(payload, status_code=200):
    return httpx.Response(
        status_code,
        headers={"content-type": "application/json"},
        content=json.dumps(payload).encode("utf-8"),
    )


class CapabilityHttpProviderTests(unittest.TestCase):
    def test_http_voice_capabilities_report_remote_health(self):
        def handler(request):
            if request.url.path == "/api/capabilities/voice.tts.edge/health":
                return _json_response(
                    {
                        "capability_id": "voice.tts.edge",
                        "kind": "tts",
                        "provider": "edge_tts",
                        "transport": "http",
                        "status": "ready",
                        "reason": "",
                    }
                )
            return _json_response({"status": "ok"})

        client = HttpCapabilityClient(
            base_url="http://voice.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_voice_capabilities(base_url="http://voice.test", client=client))
        )

        capability = service.get_capability("voice.tts.edge")

        self.assertEqual(capability["transport"], "http")
        self.assertEqual(capability["status"], "ready")
        self.assertEqual(capability["metadata"]["provider_base_url"], "http://voice.test")

    def test_http_voice_invocation_delegates_to_remote_provider(self):
        def handler(request):
            self.assertEqual(request.url.path, "/api/capabilities/voice.tts.edge/invoke")
            payload = json.loads(request.content.decode("utf-8"))
            self.assertEqual(payload["text"], "hello")
            return _json_response(
                {
                    "ok": True,
                    "capability_id": "voice.tts.edge",
                    "provider": "edge_tts",
                    "result": {"media_type": "audio/mpeg", "audio_base64": "QUJD"},
                }
            )

        client = HttpCapabilityClient(
            base_url="http://voice.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_voice_capabilities(base_url="http://voice.test", client=client))
        )

        result = service.invoke("voice.tts.edge", {"text": "hello"})

        self.assertTrue(result["ok"])
        self.assertEqual(result["result"]["audio_base64"], "QUJD")

    def test_http_voice_health_handles_unreachable_provider(self):
        def handler(request):
            raise httpx.ConnectError("connect failed", request=request)

        client = HttpCapabilityClient(
            base_url="http://voice.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_voice_capabilities(base_url="http://voice.test", client=client))
        )

        health = service.get_capability_health("voice.asr.vosk")

        self.assertEqual(health["status"], "unreachable")
        self.assertEqual(health["error"]["code"], "CAPABILITY_PROVIDER_UNREACHABLE")

    def test_heartbeat_reports_provider_and_capability_status(self):
        def handler(request):
            if request.url.path == "/health":
                return _json_response({"status": "ok", "service": "unifiedTTSandASR"})
            if request.url.path.endswith("/health"):
                capability_id = request.url.path.split("/")[-2]
                return _json_response(
                    {
                        "capability_id": capability_id,
                        "provider": "edge_tts" if capability_id.endswith("edge") else "vosk_server",
                        "transport": "http",
                        "status": "ready",
                        "reason": "",
                    }
                )
            return _json_response({})

        client = HttpCapabilityClient(
            base_url="http://voice.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_voice_capabilities(base_url="http://voice.test", client=client))
        )

        heartbeat = service.get_provider_heartbeat()

        self.assertEqual(heartbeat["contract_version"], "capability-runtime-v1")
        self.assertEqual(heartbeat["providers"][0]["status"], "ok")
        self.assertEqual(len(heartbeat["providers"][0]["capabilities"]), 2)

    def test_http_knowledge_capabilities_report_remote_health(self):
        def handler(request):
            if request.url.path == "/health":
                return _json_response({"status": "ok", "service": "unifiedKnowledgeProvider"})
            self.assertEqual(request.url.path, "/api/catalog")
            return _json_response(
                {
                    "status": "ready",
                    "catalog": {
                        "knowledge_bases": [
                            {"id": "kb-refunds", "status": "ready", "version": "2026.06"},
                        ],
                        "graphs": [],
                    },
                }
            )

        client = HttpCapabilityClient(
            base_url="http://knowledge.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_knowledge_capabilities(base_url="http://knowledge.test", client=client))
        )

        payload = service.list_capabilities()
        capability_ids = {item["capability_id"] for item in payload["capabilities"]}
        rag = next(item for item in payload["capabilities"] if item["capability_id"] == "knowledge.rag.retrieve")

        self.assertEqual(
            capability_ids,
            {"knowledge.rag.retrieve", "knowledge.graph.query"},
        )
        self.assertEqual(rag["kind"], "rag")
        self.assertEqual(rag["transport"], "http")
        self.assertEqual(rag["status"], "ready")
        self.assertEqual(rag["metadata"]["provider_base_url"], "http://knowledge.test")
        health = service.get_capability_health("knowledge.rag.retrieve")
        readiness = health["provider_health"]["governance_readiness"]
        self.assertEqual(readiness["overall_status"], "ready")
        self.assertEqual(readiness["rag_retrieve"]["status"], "ready")
        self.assertTrue(readiness["rag_retrieve"]["usable_for_explicit_calls"])
        self.assertEqual(readiness["graph_query"]["status"], "gated")
        self.assertEqual(readiness["default_chat_grounding"]["status"], "gated")
        self.assertEqual(readiness["source_catalog"]["source_count"], 1)

    def test_http_knowledge_capabilities_surface_catalog_readiness(self):
        def handler(request):
            if request.url.path == "/health":
                return _json_response({"status": "ok", "service": "unifiedKnowledgeProvider"})
            self.assertEqual(request.url.path, "/api/catalog")
            return _json_response(
                {
                    "status": "degraded",
                    "catalog": {
                        "knowledge_bases": [
                            {"id": "kb-refunds", "status": "ready", "version": "2026.06"},
                            {"id": "kb-claims", "status": "degraded", "version": "2026.06"},
                        ],
                        "graphs": [
                            {"id": "graph-orders", "status": "ready", "version": "2026.06"},
                        ],
                    },
                }
            )

        client = HttpCapabilityClient(
            base_url="http://knowledge.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_knowledge_capabilities(base_url="http://knowledge.test", client=client))
        )

        heartbeat = service.get_provider_heartbeat()
        provider = heartbeat["providers"][0]
        capability_health = provider["capabilities"][0]

        self.assertEqual(provider["status"], "degraded")
        self.assertEqual(capability_health["status"], "degraded")
        self.assertEqual(capability_health["provider_health"]["catalog_summary"]["status"], "degraded")
        self.assertEqual(capability_health["provider_health"]["catalog_summary"]["knowledge_base_count"], 2)
        self.assertEqual(capability_health["provider_health"]["catalog_summary"]["graph_count"], 1)
        self.assertEqual(capability_health["provider_health"]["catalog_summary"]["source_count"], 3)
        self.assertIn("kb-claims", capability_health["provider_health"]["catalog_summary"]["degraded_sources"])
        self.assertEqual(capability_health["provider_health"]["catalog"]["knowledge_bases"][0]["id"], "kb-refunds")
        readiness = capability_health["provider_health"]["governance_readiness"]
        self.assertEqual(readiness["overall_status"], "degraded")
        self.assertEqual(readiness["rag_retrieve"]["status"], "ready")
        self.assertEqual(readiness["source_catalog"]["status"], "degraded")
        self.assertIn("kb-claims", readiness["source_catalog"]["degraded_sources"])
        self.assertEqual(readiness["boundaries"]["source_binding_automation"], "disabled")

    def test_http_knowledge_rag_invocation_preserves_citations(self):
        def handler(request):
            self.assertEqual(request.url.path, "/api/rag/retrieve")
            payload = json.loads(request.content.decode("utf-8"))
            self.assertEqual(payload["query"], "refund?")
            return _json_response(
                {
                    "ok": True,
                    "result": {
                        "answer_context": "refund context",
                        "documents": [
                            {
                                "source_id": "refund_policy_docs",
                                "document_id": "refund_policy_2026",
                                "title": "Refund Policy",
                                "snippet": "refund snippet",
                                "score": 0.86,
                                "citation": "refund_policy_2026#section-3",
                            }
                        ],
                    },
                }
            )

        client = HttpCapabilityClient(
            base_url="http://knowledge.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_knowledge_capabilities(base_url="http://knowledge.test", client=client))
        )

        result = service.invoke("knowledge.rag.retrieve", {"query": "refund?"})

        self.assertTrue(result["ok"])
        self.assertEqual(result["capability_id"], "knowledge.rag.retrieve")
        self.assertEqual(result["result"]["answer_context"], "refund context")
        self.assertEqual(result["result"]["documents"][0]["citation"], "refund_policy_2026#section-3")

    def test_http_knowledge_graph_invocation_preserves_graph_evidence(self):
        def handler(request):
            self.assertEqual(request.url.path, "/api/graph/query")
            return _json_response(
                {
                    "ok": True,
                    "result": {
                        "graph_id": "ecommerce_order_graph",
                        "entities": [{"id": "order-1"}],
                        "relations": [],
                        "paths": [],
                        "evidence": [{"source": "graph"}],
                    },
                }
            )

        client = HttpCapabilityClient(
            base_url="http://knowledge.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_knowledge_capabilities(base_url="http://knowledge.test", client=client))
        )

        result = service.invoke("knowledge.graph.query", {"graph_id": "ecommerce_order_graph"})

        self.assertTrue(result["ok"])
        self.assertEqual(result["capability_id"], "knowledge.graph.query")
        self.assertEqual(result["result"]["graph_id"], "ecommerce_order_graph")
        self.assertEqual(result["result"]["entities"][0]["id"], "order-1")

    def test_http_knowledge_smoke_uses_health_catalog_and_retrieve_without_chat(self):
        calls: list[str] = []

        def handler(request):
            calls.append(request.url.path)
            if request.url.path == "/health":
                return _json_response({"status": "ok", "service": "unifiedKnowledgeProvider"})
            if request.url.path == "/api/catalog":
                return _json_response(
                    {
                        "status": "ready",
                        "catalog": {
                            "knowledge_bases": [
                                {"id": "kb-refunds", "status": "ready", "version": "2026.06"},
                            ],
                            "graphs": [],
                        },
                    }
                )
            if request.url.path == "/api/rag/retrieve":
                payload = json.loads(request.content.decode("utf-8"))
                self.assertEqual(payload["query"], "refund policy")
                return _json_response(
                    {
                        "ok": True,
                        "result": {
                            "answer_context": "refund policy context",
                            "documents": [
                                {
                                    "source_id": "kb-refunds",
                                    "document_id": "refund-policy-2026",
                                    "title": "Refund Policy",
                                    "snippet": "refund snippet",
                                    "score": 0.91,
                                    "citation": "refund-policy-2026#section-2",
                                }
                            ],
                        },
                    }
                )
            self.fail(f"Unexpected provider path in smoke test: {request.url.path}")

        client = HttpCapabilityClient(
            base_url="http://knowledge.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_knowledge_capabilities(base_url="http://knowledge.test", client=client))
        )

        heartbeat = service.get_provider_heartbeat()
        self.assertEqual(heartbeat["providers"][0]["status"], "ready")
        self.assertEqual(heartbeat["providers"][0]["capabilities"][0]["provider_health"]["catalog_summary"]["source_count"], 1)

        result = service.invoke("knowledge.rag.retrieve", {"query": "refund policy"})
        self.assertTrue(result["ok"])
        self.assertEqual(result["result"]["documents"][0]["citation"], "refund-policy-2026#section-2")
        self.assertNotIn("/api/chat", calls)

    def test_http_knowledge_heartbeat_survives_unreachable_provider(self):
        def handler(request):
            raise httpx.ConnectError("connect failed", request=request)

        client = HttpCapabilityClient(
            base_url="http://knowledge.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_knowledge_capabilities(base_url="http://knowledge.test", client=client))
        )

        heartbeat = service.get_provider_heartbeat()

        self.assertEqual(heartbeat["providers"][0]["status"], "unreachable")
        self.assertEqual(heartbeat["providers"][0]["error"]["code"], "CAPABILITY_PROVIDER_UNREACHABLE")
        readiness = heartbeat["providers"][0]["capabilities"][0]["provider_health"]["governance_readiness"]
        self.assertEqual(readiness["overall_status"], "unreachable")
        self.assertEqual(readiness["rag_retrieve"]["status"], "unreachable")
        self.assertEqual(readiness["error"]["code"], "CAPABILITY_PROVIDER_UNREACHABLE")
        self.assertEqual(readiness["default_chat_grounding"]["status"], "gated")

    def test_heartbeat_opens_circuit_after_repeated_failures(self):
        call_count = {"health": 0}

        def handler(request):
            if request.url.path == "/health":
                call_count["health"] += 1
                raise httpx.ConnectError("connect failed", request=request)
            return _json_response({})

        client = HttpCapabilityClient(
            base_url="http://voice.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_voice_capabilities(base_url="http://voice.test", client=client))
        )
        service._heartbeat_failure_threshold = 2
        service._heartbeat_cooldown_seconds = 60.0

        first = service.get_provider_heartbeat()
        second = service.get_provider_heartbeat()
        third = service.get_provider_heartbeat()

        self.assertEqual(first["providers"][0]["circuit_breaker"]["state"], "closed")
        self.assertEqual(second["providers"][0]["circuit_breaker"]["state"], "open")
        self.assertEqual(third["providers"][0]["circuit_breaker"]["state"], "open")
        self.assertEqual(call_count["health"], 2)

    def test_heartbeat_circuit_recovers_after_cooldown(self):
        call_count = {"health": 0}

        def handler(request):
            if request.url.path == "/health":
                call_count["health"] += 1
                if call_count["health"] == 1:
                    raise httpx.ConnectError("connect failed", request=request)
                return _json_response({"status": "ok"})
            return _json_response({})

        client = HttpCapabilityClient(
            base_url="http://voice.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_voice_capabilities(base_url="http://voice.test", client=client))
        )
        service._heartbeat_failure_threshold = 1
        service._heartbeat_cooldown_seconds = 0.01

        opened = service.get_provider_heartbeat()
        self.assertEqual(opened["providers"][0]["circuit_breaker"]["state"], "open")

        import time

        time.sleep(0.02)
        recovered = service.get_provider_heartbeat()
        self.assertEqual(recovered["providers"][0]["status"], "ok")
        self.assertEqual(recovered["providers"][0]["circuit_breaker"]["state"], "closed")
        self.assertEqual(call_count["health"], 2)

    def test_http_paddleocr_capability_maps_to_paddlex_ocr_endpoint(self):
        def handler(request):
            if request.url.path == "/health":
                return _json_response({"errorCode": 0, "errorMsg": "Healthy"})
            self.assertEqual(request.url.path, "/ocr")
            payload = json.loads(request.content.decode("utf-8"))
            self.assertEqual(payload["file"], "QUJD")
            self.assertEqual(payload["fileType"], 1)
            self.assertFalse(payload["visualize"])
            return _json_response(
                {
                    "errorCode": 0,
                    "errorMsg": "Success",
                    "result": {
                        "ocrResults": [
                            {
                                "prunedResult": {
                                    "rec_texts": ["hello", "world"],
                                    "rec_scores": [0.98, 0.96],
                                    "rec_boxes": [[1, 2, 3, 4], [5, 6, 7, 8]],
                                },
                                "ocrImage": None,
                            }
                        ]
                    },
                }
            )

        client = HttpCapabilityClient(
            base_url="http://paddleocr.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_paddleocr_capabilities(base_url="http://paddleocr.test", client=client))
        )

        result = service.invoke(
            "document.ocr.extract",
            {"file_base64": "QUJD", "media_type": "image/png"},
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["capability_id"], "document.ocr.extract")
        self.assertEqual(result["provider"], "paddleocr")
        self.assertEqual(result["result"]["text"], "hello\nworld")
        self.assertEqual(result["result"]["pages"][0]["page_number"], 1)
        self.assertEqual(result["result"]["blocks"][1]["text"], "world")
        self.assertEqual(result["result"]["tables"], [])
        self.assertEqual(result["result"]["artifacts"], [])
        self.assertEqual(result["result"]["warnings"], [])
        self.assertEqual(result["result"]["raw"]["ocrResults"][0]["prunedResult"]["rec_texts"][0], "hello")

    def test_http_paddleocr_capability_maps_pdf_file_type(self):
        def handler(request):
            if request.url.path == "/health":
                return _json_response({"errorCode": 0, "errorMsg": "Healthy"})
            payload = json.loads(request.content.decode("utf-8"))
            self.assertEqual(payload["fileType"], 0)
            return _json_response(
                {
                    "errorCode": 0,
                    "errorMsg": "Success",
                    "result": {"ocrResults": [{"prunedResult": {"rec_texts": ["pdf page"]}}]},
                }
            )

        client = HttpCapabilityClient(
            base_url="http://paddleocr.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_paddleocr_capabilities(base_url="http://paddleocr.test", client=client))
        )

        result = service.invoke(
            "document.ocr.extract",
            {"file_base64": "JVBERg==", "media_type": "application/pdf"},
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["result"]["pages"][0]["text"], "pdf page")
        self.assertEqual(result["result"]["warnings"], [])

    def test_http_paddleocr_empty_result_emits_warnings(self):
        def handler(request):
            if request.url.path == "/health":
                return _json_response({"errorCode": 0, "errorMsg": "Healthy"})
            return _json_response(
                {
                    "errorCode": 0,
                    "errorMsg": "Success",
                    "result": {},
                }
            )

        client = HttpCapabilityClient(
            base_url="http://paddleocr.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_paddleocr_capabilities(base_url="http://paddleocr.test", client=client))
        )

        result = service.invoke(
            "document.ocr.extract",
            {"file_base64": "QUJD", "media_type": "image/png"},
        )

        self.assertTrue(result["ok"])
        self.assertIn("missing ocrResults", result["result"]["warnings"][0])
        self.assertIn("No OCR text detected", result["result"]["warnings"][1])

    def test_http_paddleocr_unreachable_health_is_structured(self):
        def handler(request):
            raise httpx.ConnectError("connect failed", request=request)

        client = HttpCapabilityClient(
            base_url="http://paddleocr.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_paddleocr_capabilities(base_url="http://paddleocr.test", client=client))
        )

        health = service.get_capability_health("document.ocr.extract")

        self.assertEqual(health["status"], "unreachable")
        self.assertEqual(health["error"]["code"], "CAPABILITY_PROVIDER_UNREACHABLE")

    def test_http_layout_capability_maps_request_and_normalizes(self):
        def handler(request):
            if request.url.path == "/health":
                return _json_response({"errorCode": 0, "errorMsg": "Healthy"})
            self.assertEqual(request.url.path, "/layout-parsing")
            payload = json.loads(request.content.decode("utf-8"))
            self.assertEqual(payload["fileType"], 0)
            self.assertEqual(payload["outputFormat"], "markdown")
            self.assertTrue(payload["includeTables"])
            return _json_response(
                {
                    "errorCode": 0,
                    "result": {
                        "layoutParsingResults": [
                            {
                                "markdown": {"text": "# title"},
                                "prunedResult": {
                                    "layouts": [{"type": "title", "text": "title"}],
                                    "table_res_list": [{"rows": 2}],
                                },
                            }
                        ],
                    },
                }
            )

        client = HttpCapabilityClient(
            base_url="http://paddleocr.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_layout_capabilities(base_url="http://paddleocr.test", client=client))
        )

        result = service.invoke(
            "document.layout.parse",
            {"file_base64": "JVBERg==", "media_type": "application/pdf", "include_tables": True},
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["result"]["markdown"], "# title")
        self.assertEqual(len(result["result"]["tables"]), 1)
        self.assertEqual(len(result["result"]["elements"]), 1)
        self.assertEqual(len(result["result"]["pages"]), 1)
        self.assertEqual(result["result"]["warnings"], [])

    def test_http_layout_rejects_unsupported_media_type(self):
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_layout_capabilities(base_url="http://paddleocr.test"))
        )
        result = service.invoke(
            "document.layout.parse",
            {"file_base64": "AAA=", "media_type": "text/plain"},
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "LAYOUT_UNSUPPORTED_MEDIA_TYPE")

    def test_http_layout_rejects_invalid_output_format(self):
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_layout_capabilities(base_url="http://paddleocr.test"))
        )
        result = service.invoke(
            "document.layout.parse",
            {"file_base64": "AAA=", "media_type": "application/pdf", "output_format": "html"},
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "LAYOUT_INVALID_OUTPUT_FORMAT")

    def test_http_layout_rejects_non_positive_max_pages(self):
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_layout_capabilities(base_url="http://paddleocr.test"))
        )
        result = service.invoke(
            "document.layout.parse",
            {"file_base64": "AAA=", "media_type": "application/pdf", "max_pages": 0},
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "LAYOUT_INVALID_INPUT")

    def test_http_layout_normalization_supports_fallback_fields(self):
        def handler(request):
            if request.url.path == "/health":
                return _json_response({"errorCode": 0, "errorMsg": "Healthy"})
            return _json_response(
                {
                    "errorCode": 0,
                    "result": {
                        "text": "fallback text",
                        "layout": [{"type": "paragraph"}],
                        "tableResults": [{"id": "t1"}],
                        "pageResults": [{"page_number": 1}],
                    },
                }
            )

        client = HttpCapabilityClient(
            base_url="http://paddleocr.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_layout_capabilities(base_url="http://paddleocr.test", client=client))
        )

        result = service.invoke(
            "document.layout.parse",
            {"file_base64": "AAA=", "media_type": "image/png"},
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["result"]["markdown"], "fallback text")
        self.assertEqual(len(result["result"]["elements"]), 1)
        self.assertEqual(len(result["result"]["tables"]), 1)

    def test_http_layout_capability_supports_custom_invoke_path(self):
        def handler(request):
            if request.url.path == "/health":
                return _json_response({"errorCode": 0, "errorMsg": "Healthy"})
            self.assertEqual(request.url.path, "/custom-layout")
            return _json_response({"errorCode": 0, "result": {"layoutParsingResults": []}})

        client = HttpCapabilityClient(
            base_url="http://paddleocr.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(
                build_http_layout_capabilities(
                    base_url="http://paddleocr.test",
                    invoke_path="/custom-layout",
                    client=client,
                )
            )
        )

        result = service.invoke(
            "document.layout.parse",
            {"file_base64": "AAA=", "media_type": "image/png"},
        )

        self.assertTrue(result["ok"])

    def test_http_vlm_capability_maps_request_and_normalizes(self):
        def handler(request):
            if request.url.path == "/health":
                return _json_response({"status": "ok"})
            self.assertEqual(request.url.path, "/vlm")
            payload = json.loads(request.content.decode("utf-8"))
            self.assertEqual(payload["fileType"], 0)
            self.assertEqual(payload["task"], "summarize")
            self.assertEqual(payload["maxPages"], 3)
            return _json_response(
                {
                    "errorCode": 0,
                    "result": {
                        "summary": "document summary",
                        "sections": [{"title": "Intro"}],
                        "entities": [{"name": "Acme"}],
                        "answers": [{"value": "ok"}],
                        "evidence": [{"page": 1}],
                    },
                }
            )

        client = HttpCapabilityClient(
            base_url="http://vlm.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_document_vlm_capabilities(base_url="http://vlm.test", client=client))
        )
        result = service.invoke(
            "document.vlm.parse",
            {
                "file_base64": "JVBERg==",
                "media_type": "application/pdf",
                "task": "summarize",
                "max_pages": 3,
            },
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["result"]["summary"], "document summary")
        self.assertEqual(len(result["result"]["sections"]), 1)
        self.assertEqual(result["result"]["warnings"], [])

    def test_http_vlm_rejects_unsupported_media_type(self):
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_document_vlm_capabilities(base_url="http://vlm.test"))
        )
        result = service.invoke(
            "document.vlm.parse",
            {"file_base64": "AAA=", "media_type": "text/plain", "task": "summarize"},
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "VLM_UNSUPPORTED_MEDIA_TYPE")

    def test_http_vlm_rejects_unsupported_task(self):
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_document_vlm_capabilities(base_url="http://vlm.test"))
        )
        result = service.invoke(
            "document.vlm.parse",
            {"file_base64": "AAA=", "media_type": "application/pdf", "task": "translate"},
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "VLM_UNSUPPORTED_TASK")

    def test_http_vlm_requires_question_for_qa_task(self):
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_document_vlm_capabilities(base_url="http://vlm.test"))
        )
        result = service.invoke(
            "document.vlm.parse",
            {"file_base64": "AAA=", "media_type": "application/pdf", "task": "qa"},
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "VLM_INVALID_INPUT")

    def test_http_vlm_supports_custom_invoke_path(self):
        def handler(request):
            if request.url.path == "/health":
                return _json_response({"status": "ok"})
            self.assertEqual(request.url.path, "/custom-vlm")
            return _json_response({"errorCode": 0, "result": {"summary": "ok"}})

        client = HttpCapabilityClient(
            base_url="http://vlm.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(
                build_http_document_vlm_capabilities(
                    base_url="http://vlm.test",
                    invoke_path="/custom-vlm",
                    client=client,
                )
            )
        )
        result = service.invoke(
            "document.vlm.parse",
            {"file_base64": "AAA=", "media_type": "application/pdf", "task": "summarize"},
        )
        self.assertTrue(result["ok"])

    def test_http_vlm_normalizes_layout_parsing_results(self):
        def handler(request):
            if request.url.path == "/health":
                return _json_response({"status": "ok"})
            return _json_response(
                {
                    "errorCode": 0,
                    "result": {
                        "layoutParsingResults": [
                            {
                                "markdown": {"text": "Page1 content"},
                                "prunedResult": {"layouts": [{"label": "text"}]},
                            },
                            {
                                "markdown": {"text": "Page2 content"},
                                "prunedResult": {"layouts": [{"label": "table"}, {"label": "text"}]},
                            },
                        ]
                    },
                }
            )

        client = HttpCapabilityClient(
            base_url="http://vlm.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_document_vlm_capabilities(base_url="http://vlm.test", client=client))
        )
        result = service.invoke(
            "document.vlm.parse",
            {"file_base64": "AAA=", "media_type": "application/pdf", "task": "summarize"},
        )
        self.assertTrue(result["ok"])
        self.assertIn("Page1 content", result["result"]["summary"])
        self.assertEqual(len(result["result"]["sections"]), 2)
        self.assertEqual(result["result"]["evidence"][0]["layout_count"], 1)

    def test_http_vlm_async_submit_and_status(self):
        def handler(request):
            if request.url.path == "/health":
                return _json_response({"status": "ok"})
            if request.url.path == "/api/vlm/jobs":
                payload = json.loads(request.content.decode("utf-8"))
                self.assertEqual(payload["task"], "summarize")
                return _json_response({"result": {"job_id": "job-1", "status": "queued", "progress": 0.1}})
            if request.url.path == "/api/vlm/jobs/job-1":
                return _json_response({"result": {"job_id": "job-1", "status": "running", "progress": 0.6}})
            raise AssertionError(f"Unexpected path: {request.url.path}")

        client = HttpCapabilityClient(
            base_url="http://vlm.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_document_vlm_capabilities(base_url="http://vlm.test", client=client))
        )

        submit = service.invoke(
            "document.vlm.parse.async",
            {"operation": "submit", "file_base64": "AAA=", "media_type": "application/pdf", "task": "summarize"},
        )
        self.assertTrue(submit["ok"])
        self.assertEqual(submit["result"]["job_id"], "job-1")
        self.assertEqual(submit["result"]["status"], "queued")

        status = service.invoke(
            "document.vlm.parse.async",
            {"operation": "status", "job_id": "job-1"},
        )
        self.assertTrue(status["ok"])
        self.assertEqual(status["result"]["status"], "running")
        self.assertEqual(status["result"]["progress"], 0.6)

    def test_http_vlm_async_status_requires_job_id(self):
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_document_vlm_capabilities(base_url="http://vlm.test"))
        )
        result = service.invoke("document.vlm.parse.async", {"operation": "status"})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "VLM_ASYNC_MISSING_JOB_ID")

    def test_http_vlm_async_normalizes_status_alias(self):
        def handler(request):
            if request.url.path == "/health":
                return _json_response({"status": "ok"})
            if request.url.path == "/api/vlm/jobs":
                return _json_response({"result": {"job_id": "job-alias", "status": "pending", "progress": 0}})
            raise AssertionError(f"Unexpected path: {request.url.path}")

        client = HttpCapabilityClient(
            base_url="http://vlm.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_document_vlm_capabilities(base_url="http://vlm.test", client=client))
        )

        result = service.invoke(
            "document.vlm.parse.async",
            {"operation": "submit", "file_base64": "AAA=", "media_type": "application/pdf", "task": "summarize"},
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["result"]["status"], "queued")

    def test_http_vlm_async_uses_configured_paths(self):
        def handler(request):
            if request.url.path == "/health":
                return _json_response({"status": "ok"})
            if request.url.path == "/custom/jobs":
                return _json_response({"result": {"job_id": "job-2", "status": "running", "progress": 0.3}})
            if request.url.path == "/custom/jobs/job-2":
                return _json_response({"result": {"job_id": "job-2", "status": "success", "progress": 1.0}})
            raise AssertionError(f"Unexpected path: {request.url.path}")

        client = HttpCapabilityClient(
            base_url="http://vlm.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(
                build_http_document_vlm_capabilities(
                    base_url="http://vlm.test",
                    client=client,
                    async_submit_path="/custom/jobs",
                    async_status_path_template="/custom/jobs/{job_id}",
                )
            )
        )

        submit = service.invoke(
            "document.vlm.parse.async",
            {"operation": "submit", "file_base64": "AAA=", "media_type": "application/pdf", "task": "summarize"},
        )
        self.assertTrue(submit["ok"])
        self.assertEqual(submit["result"]["job_id"], "job-2")
        self.assertEqual(submit["result"]["status"], "running")

        status = service.invoke("document.vlm.parse.async", {"operation": "status", "job_id": "job-2"})
        self.assertTrue(status["ok"])
        self.assertEqual(status["result"]["status"], "succeeded")


if __name__ == "__main__":
    unittest.main()
