from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import httpx

from backend.capability_runtime.document_rag_local_readiness import (
    ReadinessCommandResult,
    build_document_rag_local_readiness,
    export_document_rag_local_readiness,
)


class DocumentRagLocalReadinessTests(unittest.TestCase):
    def test_readiness_go_when_services_source_and_command_are_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _provider_repo(Path(tmp))
            report = export_document_rag_local_readiness(
                output_dir=Path(tmp) / "out",
                ocr_base_url="http://ocr.local",
                ocr_profile="gpu",
                ocr_timeout_seconds=180,
                provider_base_url="http://rag.local",
                source_id="company_profile_2025_trial",
                provider_repo_path=repo,
                provider_python="python",
                transport=_transport(source_visible=True),
                command_runner=_command_runner(ok=True),
            )

            self.assertEqual(report.decision, "go")
            self.assertEqual(report.reason_code, "document_rag_local_readiness_ready")
            self.assertTrue(report.json_path.exists())
            self.assertTrue(report.markdown_path.exists())
            self.assertEqual(report.summary["document_parse_status"], "not_run")
            self.assertEqual(report.summary["provider_ingestion_status"], "not_run")
            self.assertEqual(report.summary["graph_execution_status"], "not_executed")

    def test_readiness_accepts_provider_knowledge_bases_catalog_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _provider_repo(Path(tmp))
            report = build_document_rag_local_readiness(
                ocr_base_url="http://ocr.local",
                ocr_profile="gpu",
                ocr_timeout_seconds=180,
                provider_base_url="http://rag.local",
                source_id="company_profile_2025_trial",
                provider_repo_path=repo,
                provider_python="python",
                transport=_transport(source_visible=True, catalog_shape="knowledge_bases"),
                command_runner=_command_runner(ok=True),
            )

            self.assertEqual(report.decision, "go")

    def test_readiness_reviews_for_cpu_low_timeout_and_missing_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _provider_repo(Path(tmp))
            report = build_document_rag_local_readiness(
                ocr_base_url="http://ocr.local",
                ocr_profile="cpu",
                ocr_timeout_seconds=30,
                provider_base_url="http://rag.local",
                source_id="company_profile_2025_trial",
                provider_repo_path=repo,
                provider_python="python",
                transport=_transport(source_visible=False),
                command_runner=_command_runner(ok=True),
            )

            self.assertEqual(report.decision, "review")
            self.assertIn(report.reason_code, {"ocr_timeout_below_large_pdf_recommendation", "source_not_visible"})
            reason_codes = {check.reason_code for check in report.checks}
            self.assertIn("source_not_visible", reason_codes)
            self.assertIn("increase_OCR_CAPABILITY_PROVIDER_TIMEOUT_SECONDS_for_large_pdfs", report.recommended_actions)

    def test_readiness_blocks_when_ocr_provider_is_unreachable(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _provider_repo(Path(tmp))
            report = build_document_rag_local_readiness(
                ocr_base_url="http://ocr.local",
                ocr_profile="gpu",
                ocr_timeout_seconds=180,
                provider_base_url="http://rag.local",
                source_id="company_profile_2025_trial",
                provider_repo_path=repo,
                provider_python="python",
                transport=_transport(ocr_ready=False),
                command_runner=_command_runner(ok=True),
            )

            self.assertEqual(report.decision, "blocked")
            self.assertEqual(report.reason_code, "ocr_provider_unreachable")

    def test_readiness_blocks_when_provider_repo_is_missing(self):
        report = build_document_rag_local_readiness(
            ocr_base_url="http://ocr.local",
            ocr_profile="gpu",
            ocr_timeout_seconds=180,
            provider_base_url="http://rag.local",
            source_id="company_profile_2025_trial",
            provider_repo_path=Path("Z:/missing/provider"),
            provider_python="python",
            transport=_transport(source_visible=True),
            command_runner=_should_not_run_command,
        )

        self.assertEqual(report.decision, "blocked")
        self.assertEqual(report.reason_code, "provider_repo_path_missing")

    def test_readiness_blocks_when_provider_python_command_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _provider_repo(Path(tmp))
            report = build_document_rag_local_readiness(
                ocr_base_url="http://ocr.local",
                ocr_profile="gpu",
                ocr_timeout_seconds=180,
                provider_base_url="http://rag.local",
                source_id="company_profile_2025_trial",
                provider_repo_path=repo,
                provider_python="python",
                transport=_transport(source_visible=True),
                command_runner=_command_runner(ok=False),
            )

            self.assertEqual(report.decision, "blocked")
            self.assertEqual(report.reason_code, "provider_python_command_failed")


def _provider_repo(root: Path) -> Path:
    repo = root / "unifiedKnowledgeRAG"
    script = repo / "scripts" / "export_parser_artifact_local_ingestion_loop.py"
    script.parent.mkdir(parents=True)
    script.write_text("print('ready')\n", encoding="utf-8")
    return repo


def _transport(
    *,
    ocr_ready: bool = True,
    rag_ready: bool = True,
    source_visible: bool = True,
    catalog_shape: str = "sources",
) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url == "http://ocr.local/health":
            return httpx.Response(200, json={"errorCode": 0, "status": "ok"} if ocr_ready else {"status": "down"})
        if url == "http://rag.local/health":
            return httpx.Response(200, json={"status": "ok"} if rag_ready else {"status": "down"})
        if url == "http://rag.local/api/rag/sources":
            sources = [{"source_id": "company_profile_2025_trial"}] if source_visible else []
            if catalog_shape == "knowledge_bases":
                return httpx.Response(200, json={"knowledge_bases": [{"id": item["source_id"]} for item in sources]})
            return httpx.Response(200, json={"sources": sources})
        return httpx.Response(404, json={"status": "missing"})

    return httpx.MockTransport(handler)


def _command_runner(*, ok: bool):
    def runner(**kwargs):
        return ReadinessCommandResult(
            ok=ok,
            status="ready" if ok else "blocked",
            reason_code="provider_python_command_ready" if ok else "provider_python_command_failed",
            command=["python", "--version"],
            return_code=0 if ok else 1,
            stdout="Python 3.10" if ok else "",
            stderr="" if ok else "failed",
        )

    return runner


def _should_not_run_command(**kwargs):
    raise AssertionError("command should not run")


if __name__ == "__main__":
    unittest.main()
