import json
import tempfile
import unittest
from pathlib import Path

import httpx

from backend.capability_runtime.knowledge_provider_trial import (
    build_knowledge_provider_trial_outcome,
    export_knowledge_provider_trial_outcome,
    render_knowledge_provider_trial_outcome_markdown,
)


def _json_response(payload, status_code=200):
    return httpx.Response(
        status_code,
        headers={"content-type": "application/json"},
        content=json.dumps(payload).encode("utf-8"),
    )


class KnowledgeProviderTrialTests(unittest.TestCase):
    def test_trial_passes_minimal_repo_side_access_path(self):
        calls: list[tuple[str, str]] = []

        def handler(request):
            calls.append((request.method, request.url.path))
            if request.url.path == "/health":
                return _json_response({"status": "ok", "service": "unifiedKnowledgeProvider"})
            if request.url.path == "/api/provider/manifest":
                self.assertEqual(request.headers["authorization"], "Bearer secret")
                return _json_response(
                    {
                        "provider_id": "unifiedKnowledgeProvider",
                        "contract_version": "knowledge-provider-contract-v1",
                        "capability_ids": [
                            "knowledge.rag.retrieve",
                            "knowledge.provider.source_bindings",
                        ],
                        "endpoints": {
                            "preflight": "/api/provider/preflight",
                            "rag_retrieve": "/api/rag/retrieve",
                            "source_bindings": "/api/provider/source-bindings",
                        },
                    }
                )
            if request.url.path == "/api/provider/preflight":
                return _json_response(
                    {
                        "status": "ready",
                        "bindable": True,
                        "required_capability_ids": [
                            "knowledge.rag.retrieve",
                            "knowledge.provider.source_bindings",
                        ],
                    }
                )
            if request.url.path == "/api/rag/retrieve":
                payload = json.loads(request.content.decode("utf-8"))
                self.assertEqual(payload["query"], "refund policy")
                self.assertEqual(payload["knowledge_base_ids"], ["refund_policy_docs", "logistics_faq"])
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
                                    "score": 0.91,
                                    "citation": "refund_policy_2026#section-2",
                                }
                            ],
                            "metadata": {
                                "evidence_pack": {
                                    "version": "evidence-pack-v1",
                                    "status": "answerable",
                                    "citation_policy": "use_only_returned_citations",
                                }
                            },
                        },
                    }
                )
            if request.url.path == "/api/provider/source-bindings":
                return _json_response(
                    {
                        "status": "ready",
                        "total_source_count": 2,
                        "bindable_source_count": 2,
                        "sources": [
                            {"source_id": "refund_policy_docs", "bindable": True},
                            {"source_id": "logistics_faq", "bindable": True},
                        ],
                    }
                )
            raise AssertionError(f"Unexpected path: {request.url.path}")

        outcome = build_knowledge_provider_trial_outcome(
            provider_base_url="http://knowledge.test",
            provider_api_key="secret",
            transport=httpx.MockTransport(handler),
        )

        self.assertEqual(outcome.status, "trial_passed")
        self.assertEqual(outcome.decision, "proceed_with_myprivateagent_integration_hardening")
        self.assertTrue(outcome.api_key_configured)
        self.assertEqual(outcome.summary["blocked_checks"], 0)
        self.assertEqual(outcome.summary["provider_document_rag_readiness"]["status"], "not_supplied")
        self.assertEqual(calls, [
            ("GET", "/health"),
            ("GET", "/api/provider/manifest"),
            ("GET", "/api/provider/preflight"),
            ("GET", "/api/provider/source-bindings"),
            ("POST", "/api/rag/retrieve"),
        ])

    def test_trial_reviews_non_ready_source_bindings_without_mutation(self):
        def handler(request):
            if request.url.path == "/health":
                return _json_response({"status": "ok"})
            if request.url.path == "/api/provider/manifest":
                return _json_response(_manifest_payload())
            if request.url.path == "/api/provider/preflight":
                return _json_response({"status": "ready", "bindable": True})
            if request.url.path == "/api/rag/retrieve":
                return _json_response(_retrieve_payload(pack_status="insufficient_evidence", documents=[]))
            if request.url.path == "/api/provider/source-bindings":
                return _json_response(
                    {
                        "status": "review",
                        "total_source_count": 2,
                        "bindable_source_count": 1,
                        "sources": [{"source_id": "refund_policy_docs", "bindable": True}],
                    }
                )
            raise AssertionError(f"Unexpected path: {request.url.path}")

        outcome = build_knowledge_provider_trial_outcome(
            provider_base_url="http://knowledge.test",
            transport=httpx.MockTransport(handler),
        )

        self.assertEqual(outcome.status, "trial_review")
        self.assertIn("source_bindings", outcome.summary["review_check_ids"])
        self.assertEqual(outcome.summary["source_binding_policy_owner"], "caller")

    def test_trial_records_ready_phase24_provider_readiness_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            readiness_path = Path(tmp) / "phase24-document-rag-trial-readiness.json"
            readiness_path.write_text(json.dumps(_phase24_readiness_payload()), encoding="utf-8")

            outcome = build_knowledge_provider_trial_outcome(
                provider_base_url="http://knowledge.test",
                provider_readiness_path=readiness_path,
                transport=httpx.MockTransport(_ready_provider_handler),
            )

        self.assertEqual(outcome.status, "trial_passed")
        self.assertEqual(outcome.checks[0].id, "provider_document_rag_readiness")
        self.assertEqual(outcome.checks[0].status, "ready")
        self.assertEqual(outcome.summary["provider_document_rag_readiness"]["decision"], "go")
        self.assertEqual(outcome.summary["total_checks"], 6)

    def test_trial_blocks_when_explicit_provider_readiness_artifact_is_missing(self):
        outcome = build_knowledge_provider_trial_outcome(
            provider_base_url="http://knowledge.test",
            provider_readiness_path=Path("missing-phase24-document-rag-trial-readiness.json"),
            transport=httpx.MockTransport(_ready_provider_handler),
        )

        self.assertEqual(outcome.status, "trial_blocked")
        self.assertIn("provider_document_rag_readiness", outcome.summary["blocked_check_ids"])
        self.assertEqual(
            outcome.summary["provider_document_rag_readiness"]["error"]["code"],
            "PROVIDER_READINESS_MISSING",
        )

    def test_trial_reviews_non_go_provider_readiness_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            readiness_path = Path(tmp) / "phase24-document-rag-trial-readiness.json"
            readiness_path.write_text(
                json.dumps(
                    _phase24_readiness_payload(
                        status="review",
                        decision="review",
                        trial_readiness_state="review_provider_context",
                    )
                ),
                encoding="utf-8",
            )

            outcome = build_knowledge_provider_trial_outcome(
                provider_base_url="http://knowledge.test",
                provider_readiness_path=readiness_path,
                transport=httpx.MockTransport(_ready_provider_handler),
            )

        self.assertEqual(outcome.status, "trial_review")
        self.assertIn("provider_document_rag_readiness", outcome.summary["review_check_ids"])

    def test_trial_blocks_when_provider_is_unreachable(self):
        def handler(request):
            raise httpx.ConnectError("connect failed", request=request)

        outcome = build_knowledge_provider_trial_outcome(
            provider_base_url="http://knowledge.test",
            transport=httpx.MockTransport(handler),
        )

        self.assertEqual(outcome.status, "trial_blocked")
        self.assertEqual(outcome.summary["blocked_checks"], 5)
        self.assertIn("provider_health", outcome.summary["blocked_check_ids"])

    def test_trial_export_writes_json_and_markdown(self):
        def handler(request):
            if request.url.path == "/health":
                return _json_response({"status": "ok"})
            if request.url.path == "/api/provider/manifest":
                return _json_response(_manifest_payload())
            if request.url.path == "/api/provider/preflight":
                return _json_response({"status": "ready", "bindable": True})
            if request.url.path == "/api/rag/retrieve":
                return _json_response(_retrieve_payload())
            if request.url.path == "/api/provider/source-bindings":
                return _json_response(
                    {
                        "status": "ready",
                        "total_source_count": 1,
                        "bindable_source_count": 1,
                        "sources": [{"source_id": "refund_policy_docs", "bindable": True}],
                    }
                )
            raise AssertionError(f"Unexpected path: {request.url.path}")

        outcome = export_knowledge_provider_trial_outcome(
            output_dir=Path(self._testMethodName),
            provider_base_url="http://knowledge.test",
            transport=httpx.MockTransport(handler),
        )
        try:
            payload = json.loads(outcome.json_path.read_text(encoding="utf-8"))
            markdown = outcome.markdown_path.read_text(encoding="utf-8")
            self.assertEqual(payload["status"], "trial_passed")
            self.assertIn("# Unified Knowledge Provider Trial Outcome", markdown)
            self.assertIn("Provider API key values are never written", markdown)
            self.assertIn("| `query` | `refund policy` |", markdown)
            self.assertIn("# Unified Knowledge Provider Trial Outcome", render_knowledge_provider_trial_outcome_markdown(outcome))
        finally:
            for path in [outcome.json_path, outcome.markdown_path]:
                if path and path.exists():
                    path.unlink()
            if outcome.json_path:
                outcome.json_path.parent.rmdir()


def _manifest_payload():
    return {
        "provider_id": "unifiedKnowledgeProvider",
        "contract_version": "knowledge-provider-contract-v1",
        "capability_ids": ["knowledge.rag.retrieve", "knowledge.provider.source_bindings"],
        "endpoints": {
            "preflight": "/api/provider/preflight",
            "rag_retrieve": "/api/rag/retrieve",
            "source_bindings": "/api/provider/source-bindings",
        },
    }


def _retrieve_payload(*, pack_status: str = "answerable", documents=None):
    current_documents = [
        {
            "source_id": "refund_policy_docs",
            "document_id": "refund_policy_2026",
            "title": "Refund Policy",
            "snippet": "refund snippet",
            "score": 0.91,
            "citation": "refund_policy_2026#section-2",
        }
    ] if documents is None else documents
    return {
        "ok": True,
        "result": {
            "answer_context": "refund context",
            "documents": current_documents,
            "metadata": {
                "evidence_pack": {
                    "version": "evidence-pack-v1",
                    "status": pack_status,
                    "citation_policy": "use_only_returned_citations",
                }
            },
        },
    }


def _ready_provider_handler(request):
    if request.url.path == "/health":
        return _json_response({"status": "ok"})
    if request.url.path == "/api/provider/manifest":
        return _json_response(_manifest_payload())
    if request.url.path == "/api/provider/preflight":
        return _json_response({"status": "ready", "bindable": True})
    if request.url.path == "/api/rag/retrieve":
        return _json_response(_retrieve_payload())
    if request.url.path == "/api/provider/source-bindings":
        return _json_response(
            {
                "status": "ready",
                "total_source_count": 1,
                "bindable_source_count": 1,
                "sources": [{"source_id": "refund_policy_docs", "bindable": True}],
            }
        )
    raise AssertionError(f"Unexpected path: {request.url.path}")


def _phase24_readiness_payload(
    *,
    status: str = "ready",
    decision: str = "go",
    trial_readiness_state: str = "ready_for_repo_side_document_rag_trial",
):
    return {
        "id": "phase24-document-rag-trial-readiness-v1",
        "status": status,
        "decision": decision,
        "trial_readiness_state": trial_readiness_state,
        "generated_at": "2026-06-05T07:54:27+00:00",
        "summary": {"primitive_gate_status": "ready"},
    }


if __name__ == "__main__":
    unittest.main()
