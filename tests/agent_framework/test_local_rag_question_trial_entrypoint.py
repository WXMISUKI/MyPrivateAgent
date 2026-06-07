from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.capability_runtime.local_rag_question_trial_entrypoint import (
    LOCAL_RAG_QUESTION_TRIAL_ENTRYPOINT_ID,
    LocalRagQuestionTrialReport,
    build_local_rag_question_trial_entrypoint,
    export_local_rag_question_trial_entrypoint,
)
from backend.routers.document_rag_local_trials import router


class LocalRagQuestionTrialEntrypointTests(unittest.TestCase):
    def test_answered_question_returns_go_with_citations(self):
        report = build_local_rag_question_trial_entrypoint(
            source_id="company_profile_2025_trial",
            question="公司主营业务是什么？",
            transport=_transport(answer_status="answered"),
        )

        self.assertEqual(report.decision, "go")
        self.assertEqual(report.reason_code, "rag_question_answered")
        self.assertEqual(report.answer_status, "answered")
        self.assertEqual(report.citations, ["company_profile_2025_trial#page-1"])
        self.assertEqual(report.invalid_citations, [])
        self.assertEqual(report.summary["default_chat_retrieval_injection"], "not_enabled")

    def test_insufficient_evidence_is_visible_go_result(self):
        report = build_local_rag_question_trial_entrypoint(
            source_id="company_profile_2025_trial",
            question="售后退款凭证规则是什么？",
            transport=_transport(answer_status="insufficient_evidence", documents=[]),
        )

        self.assertEqual(report.decision, "go")
        self.assertEqual(report.reason_code, "rag_question_insufficient_evidence")
        self.assertEqual(report.answer_status, "insufficient_evidence")
        self.assertEqual(report.citations, [])

    def test_invalid_citation_requires_review(self):
        report = build_local_rag_question_trial_entrypoint(
            source_id="company_profile_2025_trial",
            question="公司主营业务是什么？",
            transport=_transport(answer_status="answered", citations=["outside#page-9"]),
        )

        self.assertEqual(report.decision, "review")
        self.assertEqual(report.reason_code, "answer_citation_outside_retrieval_allowlist")
        self.assertEqual(report.invalid_citations, ["outside#page-9"])

    def test_provider_failure_blocks(self):
        report = build_local_rag_question_trial_entrypoint(
            source_id="company_profile_2025_trial",
            question="公司主营业务是什么？",
            transport=_transport(status_code=503),
        )

        self.assertEqual(report.decision, "blocked")
        self.assertEqual(report.reason_code, "retrieve_http_error")

    def test_export_writes_report_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            report = export_local_rag_question_trial_entrypoint(
                output_dir=Path(temp_dir),
                source_id="company_profile_2025_trial",
                question="公司主营业务是什么？",
                transport=_transport(answer_status="answered"),
            )

            self.assertEqual(report.id, LOCAL_RAG_QUESTION_TRIAL_ENTRYPOINT_ID)
            self.assertTrue(report.json_path.exists())
            self.assertTrue(report.markdown_path.exists())

    def test_router_runs_question_trial(self):
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        with patch(
            "backend.routers.document_rag_local_trials.export_local_rag_question_trial_entrypoint",
            return_value=_question_result("go"),
        ) as run_trial:
            response = client.post(
                "/api/document-rag/local-question-trials",
                json={
                    "source_id": "company_profile_2025_trial",
                    "question": "公司主营业务是什么？",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["id"], LOCAL_RAG_QUESTION_TRIAL_ENTRYPOINT_ID)
        self.assertEqual(run_trial.call_args.kwargs["question"], "公司主营业务是什么？")


def _transport(
    *,
    answer_status: str = "answered",
    documents: list[dict] | None = None,
    citations: list[str] | None = None,
    status_code: int = 200,
) -> httpx.MockTransport:
    active_documents = documents if documents is not None else [
        {
            "id": "doc-1",
            "text": "公司主营业务包括智慧园区、信息化系统集成和运维服务。",
            "citation": "company_profile_2025_trial#page-1",
            "score": 0.91,
        }
    ]
    active_citations = citations if citations is not None else [
        document["citation"] for document in active_documents if "citation" in document
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        if status_code >= 400:
            return httpx.Response(status_code, json={"error": {"code": "PROVIDER_HTTP_ERROR", "message": "down"}})
        if request.url.path.endswith("/api/rag/retrieve"):
            return httpx.Response(200, json={"ok": True, "result": {"documents": active_documents}})
        if request.url.path.endswith("/api/rag/answer"):
            answer = "公司主营业务包括智慧园区、信息化系统集成和运维服务。" if answer_status == "answered" else ""
            return httpx.Response(
                200,
                json={
                    "ok": True,
                    "result": {
                        "answer_status": answer_status,
                        "answer": answer,
                        "citations": active_citations if answer_status == "answered" else [],
                        "evidence_pack": {"status": "ready" if answer_status == "answered" else "insufficient_evidence"},
                    },
                },
            )
        return httpx.Response(404, json={"error": {"code": "NOT_FOUND", "message": "not found"}})

    return httpx.MockTransport(handler)


def _question_result(decision: str) -> LocalRagQuestionTrialReport:
    return LocalRagQuestionTrialReport(
        id=LOCAL_RAG_QUESTION_TRIAL_ENTRYPOINT_ID,
        generated_at="2026-06-07T00:00:00+00:00",
        provider_base_url="http://127.0.0.1:8020",
        source_id="company_profile_2025_trial",
        question="公司主营业务是什么？",
        top_k=3,
        decision=decision,
        reason_code="rag_question_answered",
        answer_status="answered",
        answer="公司主营业务包括智慧园区。",
        citations=["company_profile_2025_trial#page-1"],
        allowed_citations=["company_profile_2025_trial#page-1"],
        evidence_pack={"status": "ready"},
        summary={"final_decision": decision},
        recommended_actions=[],
        non_goals=[],
    )


if __name__ == "__main__":
    unittest.main()
