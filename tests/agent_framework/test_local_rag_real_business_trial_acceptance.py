from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from backend.capability_runtime.local_rag_real_business_trial_acceptance import (
    LOCAL_RAG_REAL_BUSINESS_TRIAL_ACCEPTANCE_ID,
    build_local_rag_real_business_trial_acceptance,
    export_local_rag_real_business_trial_acceptance,
)


class LocalRagRealBusinessTrialAcceptanceTests(unittest.TestCase):
    def test_acceptance_returns_go_for_upload_and_expected_question_modes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            upload_path = _write_json(root / "upload.json", _upload_report("go"))
            answerable_path = _write_json(root / "answerable.json", _question_report("answered"))
            negative_path = _write_json(
                root / "negative.json",
                _question_report("insufficient_evidence", answer="", citations=[]),
            )

            report = build_local_rag_real_business_trial_acceptance(
                upload_report_path=upload_path,
                question_report_paths=[answerable_path, negative_path],
                expected_modes={
                    str(answerable_path): "answerable",
                    str(negative_path): "insufficient_evidence",
                },
            )

        self.assertEqual(report.decision, "go")
        self.assertEqual(report.reason_code, "local_rag_real_business_trial_accepted")
        self.assertEqual(report.follow_up_area, "no_follow_up_required")
        self.assertEqual(report.summary["ready_question_count"], 2)
        self.assertEqual(report.summary["default_chat_retrieval_injection"], "not_enabled")

    def test_acceptance_reviews_negative_control_evidence_leak(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            upload_path = _write_json(root / "upload.json", _upload_report("go"))
            negative_path = _write_json(root / "negative.json", _question_report("answered"))

            report = build_local_rag_real_business_trial_acceptance(
                upload_report_path=upload_path,
                question_report_paths=[negative_path],
                expected_modes={str(negative_path): "insufficient_evidence"},
            )

        self.assertEqual(report.decision, "review")
        self.assertEqual(report.follow_up_area, "citation_evidence")
        self.assertEqual(report.question_cases[0].status, "review")

    def test_acceptance_blocks_missing_question_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            upload_path = _write_json(root / "upload.json", _upload_report("go"))

            report = build_local_rag_real_business_trial_acceptance(
                upload_report_path=upload_path,
                question_report_paths=[root / "missing.json"],
            )

        self.assertEqual(report.decision, "blocked")
        self.assertEqual(report.follow_up_area, "operator_flow")
        self.assertTrue(report.blockers)

    def test_acceptance_classifies_provider_unavailable_as_blocked(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            upload_path = _write_json(root / "upload.json", _upload_report("go"))
            question_path = _write_json(
                root / "question.json",
                _question_report(None, decision="blocked", reason_code="local_provider_unreachable"),
            )

            report = build_local_rag_real_business_trial_acceptance(
                upload_report_path=upload_path,
                question_report_paths=[question_path],
            )

        self.assertEqual(report.decision, "blocked")
        self.assertEqual(report.follow_up_area, "provider_availability")

    def test_export_writes_json_and_markdown(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            upload_path = _write_json(root / "upload.json", _upload_report("go"))
            question_path = _write_json(root / "question.json", _question_report("answered"))

            report = export_local_rag_real_business_trial_acceptance(
                output_dir=root / "out",
                upload_report_path=upload_path,
                question_report_paths=[question_path],
            )

            self.assertEqual(report.id, LOCAL_RAG_REAL_BUSINESS_TRIAL_ACCEPTANCE_ID)
            self.assertTrue(report.json_path.exists())
            self.assertTrue(report.markdown_path.exists())


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _upload_report(decision: str) -> dict:
    return {
        "id": "document-rag-upload-to-use-loop-v1",
        "decision": decision,
        "reason_code": f"upload_{decision}",
        "document_path": "D:/docs/company.pdf",
        "source_id": "company_profile_2025_trial",
        "provider_base_url": "http://127.0.0.1:8020",
        "summary": {
            "source_id": "company_profile_2025_trial",
            "document_path": "D:/docs/company.pdf",
            "provider_ingestion_status": "ready",
        },
    }


def _question_report(
    answer_status: str | None,
    *,
    decision: str | None = None,
    reason_code: str | None = None,
    answer: str = "公司主营业务包括智慧园区和信息化系统集成。",
    citations: list[str] | None = None,
) -> dict:
    active_decision = decision or ("go" if answer_status else "blocked")
    active_citations = citations if citations is not None else ["company_profile_2025_trial#page-1"]
    return {
        "id": "local-rag-question-trial-entrypoint-v1",
        "decision": active_decision,
        "reason_code": reason_code or (
            "rag_question_answered" if answer_status == "answered" else "rag_question_insufficient_evidence"
        ),
        "source_id": "company_profile_2025_trial",
        "provider_base_url": "http://127.0.0.1:8020",
        "question": "公司主营业务是什么？",
        "answer_status": answer_status,
        "answer": answer,
        "citations": active_citations,
        "invalid_citations": [],
        "evidence_pack": {"status": "ready" if answer_status == "answered" else "insufficient_evidence"},
    }


if __name__ == "__main__":
    unittest.main()
