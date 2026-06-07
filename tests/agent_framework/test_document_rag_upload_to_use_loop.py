from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from backend.capability_runtime.document_rag_upload_to_use_loop import (
    ProviderIngestionCommandResult,
    build_document_rag_upload_to_use_loop,
    export_document_rag_upload_to_use_loop,
)


class FakeDocumentIngestionService:
    def __init__(self, *, status: str = "succeeded", payload: dict | None = None):
        self.status = status
        self.payload = payload if payload is not None else _ocr_payload()
        self.submit_calls = []

    def submit(self, request):
        self.submit_calls.append(request)
        return SimpleNamespace(
            metadata={
                "ingest_id": "doc-ingest-1",
                "status": self.status,
                "parse_mode": request["parse_mode"],
                "capability_id": f"document.{request['parse_mode']}.extract"
                if request["parse_mode"] == "ocr"
                else "document.layout.parse",
                "provider": "paddleocr" if self.status == "succeeded" else "",
                "artifact_id": "doc-artifact-1" if self.status == "succeeded" else "",
                "warnings": [],
                "error": {} if self.status == "succeeded" else {"code": "boom"},
            }
        )

    def get_result(self, ingest_id):
        return {
            "ingestion": {"ingest_id": ingest_id},
            "artifact": {"artifact_id": "doc-artifact-1"},
            "payload": self.payload,
        }


class DocumentRagUploadToUseLoopTests(unittest.TestCase):
    def test_upload_to_use_loop_go_writes_report_and_parser_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            document_path = _write_pdf(root)

            report = export_document_rag_upload_to_use_loop(
                document_path=document_path,
                output_dir=root / "out",
                source_id="company_profile_2025_trial",
                title="公司简介 2025 trial",
                document_ingestion_service=FakeDocumentIngestionService(),
                provider_ingestion_runner=_provider_runner(ok=True),
                corpus_trial_exporter=_corpus_trial("go"),
            )

            self.assertEqual(report.decision, "go")
            self.assertEqual(report.reason_code, "document_rag_upload_to_use_ready")
            self.assertTrue(report.parser_artifact_path.exists())
            self.assertTrue(report.json_path.exists())
            self.assertTrue(report.markdown_path.exists())
            self.assertEqual(
                [step.id for step in report.steps],
                [
                    "document_ingestion",
                    "rag_handoff_artifact",
                    "provider_parser_artifact_ingestion",
                    "local_knowledge_provider_corpus_trial",
                ],
            )
            artifact_text = report.parser_artifact_path.read_text(encoding="utf-8")
            self.assertIn('"citation": "company_profile_2025_trial#page-1"', artifact_text)
            self.assertEqual(report.summary["default_chat_retrieval_injection"], "not_enabled")
            self.assertEqual(report.summary["graph_execution_status"], "not_executed")

    def test_upload_to_use_loop_blocks_when_document_ingestion_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            report = build_document_rag_upload_to_use_loop(
                document_path=_write_pdf(root),
                output_dir=root / "out",
                document_ingestion_service=FakeDocumentIngestionService(status="failed"),
                provider_ingestion_runner=_should_not_run_provider,
                corpus_trial_exporter=_should_not_run_trial,
            )

            self.assertEqual(report.decision, "blocked")
            self.assertEqual(report.reason_code, "document_ingestion_not_succeeded")
            self.assertIsNone(report.parser_artifact_path)

    def test_upload_to_use_loop_blocks_when_artifact_has_no_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            report = build_document_rag_upload_to_use_loop(
                document_path=_write_pdf(root),
                output_dir=root / "out",
                document_ingestion_service=FakeDocumentIngestionService(payload={"blocks": [], "text": ""}),
                provider_ingestion_runner=_should_not_run_provider,
                corpus_trial_exporter=_should_not_run_trial,
            )

            self.assertEqual(report.decision, "blocked")
            self.assertEqual(report.reason_code, "document_artifact_has_no_rag_text")

    def test_upload_to_use_loop_handoff_only_reviews_after_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            report = build_document_rag_upload_to_use_loop(
                document_path=_write_pdf(root),
                output_dir=root / "out",
                handoff_only=True,
                document_ingestion_service=FakeDocumentIngestionService(),
                provider_ingestion_runner=_should_not_run_provider,
                corpus_trial_exporter=_should_not_run_trial,
            )

            self.assertEqual(report.decision, "review")
            self.assertEqual(report.reason_code, "provider_ingestion_not_run_handoff_only")
            self.assertTrue(report.parser_artifact_path.exists())
            self.assertEqual(report.provider_ingestion["status"], "skipped")

    def test_upload_to_use_loop_blocks_when_provider_command_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            report = build_document_rag_upload_to_use_loop(
                document_path=_write_pdf(root),
                output_dir=root / "out",
                document_ingestion_service=FakeDocumentIngestionService(),
                provider_ingestion_runner=_provider_runner(ok=False),
                corpus_trial_exporter=_should_not_run_trial,
            )

            self.assertEqual(report.decision, "blocked")
            self.assertEqual(report.reason_code, "provider_ingestion_command_failed")

    def test_upload_to_use_loop_reviews_when_corpus_trial_reviews(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            report = build_document_rag_upload_to_use_loop(
                document_path=_write_pdf(root),
                output_dir=root / "out",
                document_ingestion_service=FakeDocumentIngestionService(),
                provider_ingestion_runner=_provider_runner(ok=True),
                corpus_trial_exporter=_corpus_trial("review", reason_code="negative_control_returned_evidence"),
            )

            self.assertEqual(report.decision, "review")
            self.assertEqual(report.reason_code, "corpus_trial_negative_control_returned_evidence")

    def test_upload_to_use_loop_blocks_when_corpus_trial_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            report = build_document_rag_upload_to_use_loop(
                document_path=_write_pdf(root),
                output_dir=root / "out",
                document_ingestion_service=FakeDocumentIngestionService(),
                provider_ingestion_runner=_provider_runner(ok=True),
                corpus_trial_exporter=_corpus_trial("blocked", reason_code="source_not_registered"),
            )

            self.assertEqual(report.decision, "blocked")
            self.assertEqual(report.reason_code, "corpus_trial_source_not_registered")


def _write_pdf(root: Path) -> Path:
    path = root / "company.pdf"
    path.write_bytes(b"%PDF-1.7 fake")
    return path


def _ocr_payload() -> dict:
    return {
        "blocks": [
            {
                "page_number": 1,
                "text": "公司主营业务包括工程咨询和数字化服务。",
            }
        ],
        "pages": [],
        "warnings": [],
    }


def _provider_runner(*, ok: bool):
    def runner(**kwargs):
        return ProviderIngestionCommandResult(
            ok=ok,
            status="ready" if ok else "blocked",
            reason_code="provider_ingestion_command_ready" if ok else "provider_ingestion_command_failed",
            command=["fake"],
            return_code=0 if ok else 1,
            stdout="ok" if ok else "",
            stderr="" if ok else "failed",
        )

    return runner


def _corpus_trial(decision: str, *, reason_code: str | None = None):
    def exporter(*, output_dir, provider_base_url, source_id, **kwargs):
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "local-knowledge-provider-corpus-trial.json"
        markdown_path = output_dir / "local-knowledge-provider-corpus-trial.md"
        json_path.write_text("{}", encoding="utf-8")
        markdown_path.write_text("# trial\n", encoding="utf-8")
        return SimpleNamespace(
            decision=decision,
            reason_code=reason_code or f"trial_{decision}",
            source_id=source_id,
            provider_base_url=provider_base_url,
            json_path=json_path,
            markdown_path=markdown_path,
            summary={"final_decision": decision},
        )

    return exporter


def _should_not_run_provider(**kwargs):
    raise AssertionError("provider ingestion should not run")


def _should_not_run_trial(**kwargs):
    raise AssertionError("corpus trial should not run")


if __name__ == "__main__":
    unittest.main()
