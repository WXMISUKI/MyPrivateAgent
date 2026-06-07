import json
import tempfile
import unittest
from pathlib import Path

import httpx

from backend.capability_runtime.local_knowledge_provider_corpus_trial import (
    CorpusTrialCase,
    build_local_knowledge_provider_corpus_trial,
    export_local_knowledge_provider_corpus_trial,
)


SOURCE_ID = "company_profile_2025_trial"
GOOD_CITATION = f"{SOURCE_ID}#chunk-1"


def _json_response(payload, status_code=200):
    return httpx.Response(
        status_code,
        headers={"content-type": "application/json"},
        content=json.dumps(payload).encode("utf-8"),
    )


class LocalKnowledgeProviderCorpusTrialTests(unittest.TestCase):
    def test_trial_go_for_registered_company_source(self):
        trial = build_local_knowledge_provider_corpus_trial(
            provider_base_url="http://knowledge.test",
            transport=httpx.MockTransport(lambda request: _response_for(request, mode="go")),
        )

        self.assertEqual(trial.decision, "go")
        self.assertEqual(trial.reason_code, "local_corpus_trial_accepted")
        self.assertEqual(trial.summary["case_count"], 5)
        self.assertEqual(trial.summary["invalid_citation_count"], 0)
        self.assertTrue(all(case.status == "ready" for case in trial.cases))

    def test_trial_blocks_when_provider_unreachable(self):
        def handler(request):
            raise httpx.ConnectError("connection refused", request=request)

        trial = build_local_knowledge_provider_corpus_trial(
            provider_base_url="http://knowledge.test",
            transport=httpx.MockTransport(handler),
        )

        self.assertEqual(trial.decision, "blocked")
        self.assertEqual(trial.reason_code, "local_provider_unreachable")
        self.assertEqual(trial.cases[0].id, "catalog_visibility")

    def test_trial_blocks_when_source_is_missing(self):
        trial = build_local_knowledge_provider_corpus_trial(
            provider_base_url="http://knowledge.test",
            source_id="missing_source",
            transport=httpx.MockTransport(lambda request: _response_for(request, mode="go")),
        )

        self.assertEqual(trial.decision, "blocked")
        self.assertEqual(trial.reason_code, "source_not_registered")
        self.assertEqual(trial.cases[0].id, "catalog_visibility")

    def test_trial_blocks_invalid_answer_citation(self):
        trial = build_local_knowledge_provider_corpus_trial(
            provider_base_url="http://knowledge.test",
            cases=[
                CorpusTrialCase(
                    id="invalid_citation",
                    query="公司主营业务是什么？",
                    expected_mode="answerable",
                    description="Answer cites outside retrieve allowlist.",
                )
            ],
            transport=httpx.MockTransport(lambda request: _response_for(request, mode="invalid_citation")),
        )

        self.assertEqual(trial.decision, "blocked")
        self.assertEqual(trial.reason_code, "answer_citation_outside_retrieval_allowlist")
        self.assertEqual(trial.cases[0].invalid_citations, [f"{SOURCE_ID}#bad"])

    def test_trial_reviews_when_answerable_case_has_no_evidence(self):
        trial = build_local_knowledge_provider_corpus_trial(
            provider_base_url="http://knowledge.test",
            cases=[
                CorpusTrialCase(
                    id="weak_case",
                    query="完全不存在的专有术语 ABCXYZ",
                    expected_mode="answerable",
                    description="Expected answerable case with no evidence.",
                )
            ],
            transport=httpx.MockTransport(lambda request: _response_for(request, mode="no_evidence")),
        )

        self.assertEqual(trial.decision, "review")
        self.assertEqual(trial.reason_code, "local_corpus_trial_needs_review")
        self.assertEqual(trial.cases[0].reason_code, "expected_answerable_evidence_missing")

    def test_trial_export_redacts_provider_api_key(self):
        requests: list[httpx.Request] = []
        secret = "secret-provider-key"

        def handler(request):
            requests.append(request)
            return _response_for(request, mode="go")

        with tempfile.TemporaryDirectory() as tmp:
            trial = export_local_knowledge_provider_corpus_trial(
                output_dir=Path(tmp),
                provider_base_url="http://knowledge.test",
                provider_api_key=secret,
                transport=httpx.MockTransport(handler),
            )
            payload = trial.json_path.read_text(encoding="utf-8")
            markdown = trial.markdown_path.read_text(encoding="utf-8")

        self.assertEqual(trial.decision, "go")
        self.assertTrue(trial.api_key_configured)
        self.assertTrue(any(request.headers.get("authorization") == f"Bearer {secret}" for request in requests))
        self.assertNotIn(secret, payload)
        self.assertNotIn(secret, markdown)


def _response_for(request, *, mode: str):
    if request.url.path == "/api/rag/sources":
        return _json_response(
            {
                "knowledge_bases": [
                    {
                        "id": SOURCE_ID,
                        "status": "ready",
                    }
                ],
                "graphs": [],
            }
        )
    if request.url.path == f"/api/rag/sources/{SOURCE_ID}/documents":
        return _json_response(
            {
                "ok": True,
                "result": {
                    "documents": [
                        {
                            "document_id": SOURCE_ID,
                            "title": "公司简介 2025 trial",
                        }
                    ]
                },
            }
        )
    if request.url.path.startswith("/api/rag/sources/"):
        return _json_response({"ok": False, "error": {"code": "UNKNOWN_SOURCE"}})
    if request.url.path == "/api/rag/retrieve":
        query = _request_query(request)
        if mode == "no_evidence" or query == "售后退款凭证规则":
            return _json_response({"ok": True, "result": {"documents": []}})
        return _json_response(
            {
                "ok": True,
                "result": {
                    "documents": [
                        {
                            "source_id": SOURCE_ID,
                            "citation": GOOD_CITATION,
                        }
                    ]
                },
            }
        )
    if request.url.path == "/api/rag/answer":
        query = _request_query(request)
        if mode == "no_evidence" or query == "售后退款凭证规则":
            return _json_response(
                {
                    "ok": True,
                    "result": {
                        "answer_status": "insufficient_evidence",
                        "citations": [],
                    },
                }
            )
        citation = f"{SOURCE_ID}#bad" if mode == "invalid_citation" else GOOD_CITATION
        return _json_response(
            {
                "ok": True,
                "result": {
                    "answer_status": "answered",
                    "citations": [citation],
                },
            }
        )
    raise AssertionError(f"Unexpected path: {request.url.path}")


def _request_query(request) -> str:
    payload = json.loads(request.content.decode("utf-8"))
    return str(payload.get("query"))


if __name__ == "__main__":
    unittest.main()
