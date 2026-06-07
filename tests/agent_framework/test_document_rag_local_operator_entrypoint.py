from __future__ import annotations

import base64
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.capability_runtime.document_rag_local_operator_entrypoint import (
    DOCUMENT_RAG_LOCAL_OPERATOR_ENTRYPOINT_ID,
    DocumentRagLocalOperatorResult,
    materialize_document_rag_operator_upload,
    run_document_rag_local_readiness_entrypoint,
    run_document_rag_local_trial_entrypoint,
)
from backend.capability_runtime.document_rag_local_readiness import DocumentRagLocalReadinessReport
from backend.capability_runtime.document_rag_upload_to_use_loop import DocumentRagUploadToUseReport
from backend.agent_server.router_registry import get_api_router_registrations
from backend.routers.document_rag_local_trials import router


class DocumentRagLocalOperatorEntrypointTests(unittest.TestCase):
    def test_readiness_entrypoint_returns_readiness_report_only(self):
        result = run_document_rag_local_readiness_entrypoint(
            source_id="company_profile_2025_trial",
            readiness_exporter=_readiness_exporter("go"),
        )

        self.assertEqual(result.decision, "go")
        self.assertEqual(result.summary["entrypoint"], "readiness")
        self.assertEqual(result.upload_to_use["status"], "not_run")
        self.assertEqual(result.summary["default_chat_retrieval_injection"], "not_enabled")

    def test_trial_short_circuits_when_readiness_is_blocked(self):
        result = run_document_rag_local_trial_entrypoint(
            document_path=Path("D:/docs/company.pdf"),
            source_id="company_profile_2025_trial",
            readiness_exporter=_readiness_exporter("blocked", "ocr_provider_unreachable"),
            upload_to_use_exporter=_should_not_run_upload,
        )

        self.assertEqual(result.decision, "blocked")
        self.assertEqual(result.reason_code, "readiness_ocr_provider_unreachable")
        self.assertEqual(result.upload_to_use["status"], "not_run")

    def test_trial_runs_upload_when_readiness_is_go(self):
        result = run_document_rag_local_trial_entrypoint(
            document_path=Path("D:/docs/company.pdf"),
            source_id="company_profile_2025_trial",
            readiness_exporter=_readiness_exporter("go"),
            upload_to_use_exporter=_upload_exporter("go"),
        )

        self.assertEqual(result.decision, "go")
        self.assertEqual(result.reason_code, "document_rag_upload_to_use_ready")
        self.assertEqual(result.summary["upload_to_use_status"], "go")
        self.assertEqual(result.upload_to_use["source_id"], "company_profile_2025_trial")

    def test_trial_summary_includes_upload_materialization_metadata(self):
        result = run_document_rag_local_trial_entrypoint(
            document_path=Path("D:/uploads/abc-company.pdf"),
            source_id="company_profile_2025_trial",
            upload_materialization={
                "filename": "company.pdf",
                "media_type": "application/pdf",
                "document_path": Path("D:/uploads/abc-company.pdf"),
                "sha256": "abc123",
                "byte_size": 7,
            },
            readiness_exporter=_readiness_exporter("go"),
            upload_to_use_exporter=_upload_exporter("go"),
        )

        self.assertEqual(result.summary["input_mode"], "uploaded_file")
        self.assertEqual(result.summary["upload_materialization"]["filename"], "company.pdf")
        self.assertEqual(result.summary["upload_materialization"]["byte_size"], 7)

    def test_trial_holds_review_readiness_when_not_allowed(self):
        result = run_document_rag_local_trial_entrypoint(
            document_path=Path("D:/docs/company.pdf"),
            source_id="company_profile_2025_trial",
            allow_review_readiness=False,
            readiness_exporter=_readiness_exporter("review", "source_not_visible"),
            upload_to_use_exporter=_should_not_run_upload,
        )

        self.assertEqual(result.decision, "review")
        self.assertEqual(result.reason_code, "readiness_source_not_visible")
        self.assertEqual(result.upload_to_use["reason_code"], "readiness_review_not_allowed")

    def test_router_readiness_response_uses_operator_contract(self):
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        with patch(
            "backend.routers.document_rag_local_trials.run_document_rag_local_readiness_entrypoint",
            return_value=_operator_result("go"),
        ):
            response = client.post("/api/document-rag/local-trials/readiness", json={"ocr_profile": "gpu"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["id"], DOCUMENT_RAG_LOCAL_OPERATOR_ENTRYPOINT_ID)

    def test_router_trial_requires_document_path(self):
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        response = client.post("/api/document-rag/local-trials", json={})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "DOCUMENT_RAG_LOCAL_TRIAL_INVALID_INPUT")

    def test_materializes_uploaded_file_with_safe_hash_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            materialized = materialize_document_rag_operator_upload(
                file_base64=base64.b64encode(b"pdf-bytes").decode("ascii"),
                filename="../company profile.pdf",
                media_type="application/pdf",
                upload_dir=Path(temp_dir),
            )

            self.assertTrue(materialized.document_path.exists())
            self.assertEqual(materialized.document_path.read_bytes(), b"pdf-bytes")
            self.assertEqual(materialized.filename, "company_profile.pdf")
            self.assertEqual(materialized.media_type, "application/pdf")
            self.assertEqual(materialized.byte_size, 9)
            self.assertTrue(materialized.document_path.name.endswith("-company_profile.pdf"))

    def test_router_trial_accepts_uploaded_file_payload(self):
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "backend.routers.document_rag_local_trials.run_document_rag_local_trial_entrypoint",
                return_value=_operator_result("go"),
            ) as run_trial:
                response = client.post(
                    "/api/document-rag/local-trials",
                    json={
                        "file_base64": base64.b64encode(b"pdf-bytes").decode("ascii"),
                        "filename": "company.pdf",
                        "media_type": "application/pdf",
                        "operator_upload_dir": temp_dir,
                    },
                )

            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["ok"])
            self.assertEqual(run_trial.call_args.kwargs["document_path"].read_bytes(), b"pdf-bytes")
            self.assertEqual(run_trial.call_args.kwargs["upload_materialization"].filename, "company.pdf")

    def test_router_trial_rejects_invalid_uploaded_file_payload(self):
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        with patch("backend.routers.document_rag_local_trials.run_document_rag_local_trial_entrypoint") as run_trial:
            response = client.post(
                "/api/document-rag/local-trials",
                json={"file_base64": "not-base64", "filename": "company.pdf", "media_type": "application/pdf"},
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "DOCUMENT_RAG_LOCAL_TRIAL_INVALID_UPLOAD")
        run_trial.assert_not_called()

    def test_router_trial_keeps_document_path_fallback(self):
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        with patch(
            "backend.routers.document_rag_local_trials.run_document_rag_local_trial_entrypoint",
            return_value=_operator_result("go"),
        ) as run_trial:
            response = client.post("/api/document-rag/local-trials", json={"document_path": "D:/docs/company.pdf"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(run_trial.call_args.kwargs["document_path"], Path("D:/docs/company.pdf"))
        self.assertIsNone(run_trial.call_args.kwargs["upload_materialization"])

    def test_router_registered_in_capabilities_group(self):
        registrations = get_api_router_registrations(route_names=["document_rag_local_trials"])

        self.assertEqual(len(registrations), 1)
        self.assertIn("capabilities", registrations[0].groups)


def _readiness_exporter(decision: str, reason_code: str | None = None):
    def exporter(**kwargs):
        return DocumentRagLocalReadinessReport(
            id="document-rag-local-readiness-v1",
            generated_at="2026-06-07T00:00:00+00:00",
            decision=decision,
            reason_code=reason_code or f"readiness_{decision}",
            ocr_base_url="http://127.0.0.1:8080",
            ocr_profile="gpu",
            ocr_timeout_seconds=180,
            provider_base_url="http://127.0.0.1:8020",
            source_id=kwargs.get("source_id") or "company_profile_2025_trial",
            provider_repo_path=Path("D:/AI/AIcode/unifiedKnowledgeRAG"),
            provider_python="conda run -n GRAPHRAG python",
            checks=[],
            summary={"final_decision": decision},
            recommended_actions=[f"action_{decision}"],
            non_goals=["does_not_execute_graphrag"],
            json_path=Path("readiness.json"),
            markdown_path=Path("readiness.md"),
        )

    return exporter


def _upload_exporter(decision: str, reason_code: str | None = None):
    def exporter(**kwargs):
        return DocumentRagUploadToUseReport(
            id="document-rag-upload-to-use-loop-v1",
            generated_at="2026-06-07T00:00:00+00:00",
            decision=decision,
            reason_code=reason_code or "document_rag_upload_to_use_ready",
            document_path=kwargs["document_path"],
            parse_mode=kwargs.get("parse_mode") or "ocr",
            source_id=kwargs.get("source_id") or "company_profile_2025_trial",
            title=kwargs.get("title") or "trial",
            query=kwargs.get("query") or "query",
            provider_base_url=kwargs.get("provider_base_url") or "http://127.0.0.1:8020",
            provider_repo_path=kwargs.get("provider_repo_path"),
            handoff_only=False,
            ingestion={},
            parser_artifact_path=Path("parser.json"),
            provider_ingestion={},
            corpus_trial={},
            steps=[],
            summary={"final_decision": decision},
            recommended_actions=[f"upload_{decision}"],
            non_goals=["does_not_execute_graphrag"],
            json_path=Path("upload.json"),
            markdown_path=Path("upload.md"),
        )

    return exporter


def _operator_result(decision: str) -> DocumentRagLocalOperatorResult:
    return DocumentRagLocalOperatorResult(
        id=DOCUMENT_RAG_LOCAL_OPERATOR_ENTRYPOINT_ID,
        generated_at="2026-06-07T00:00:00+00:00",
        decision=decision,
        reason_code=f"operator_{decision}",
        readiness={"decision": decision},
        upload_to_use={"status": "not_run"},
        summary={"final_decision": decision},
        recommended_actions=[],
        non_goals=[],
    )


def _should_not_run_upload(**kwargs):
    raise AssertionError("upload-to-use should not run")


if __name__ == "__main__":
    unittest.main()
