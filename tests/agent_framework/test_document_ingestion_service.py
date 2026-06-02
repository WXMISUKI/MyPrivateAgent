import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routers import document_ingestions
from backend.services import document_ingestion_service as service_module
from backend.services.document_artifact_service import DocumentArtifactService
from backend.services.document_ingestion_service import DocumentIngestionNotFound, DocumentIngestionService


class FakeCapabilityRuntime:
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.calls = []

    def invoke(self, capability_id, payload):
        self.calls.append((capability_id, payload))
        response = self.responses.get(capability_id)
        if callable(response):
            return response(payload)
        if response is None:
            raise LookupError(f"Capability not found: {capability_id}")
        return response


class DocumentIngestionServiceTests(unittest.TestCase):
    def test_submit_ocr_ingestion_persists_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = FakeCapabilityRuntime(
                {
                    "document.ocr.extract": {
                        "ok": True,
                        "provider": "paddleocr",
                        "result": {
                            "text": "hello",
                            "pages": [{"page_number": 1}],
                            "blocks": [],
                            "warnings": ["minor"],
                            "raw": {"drop": True},
                        },
                    }
                }
            )
            service = DocumentIngestionService(
                root_dir=root / "ingestions",
                capability_runtime=runtime,
                artifact_service=DocumentArtifactService(root_dir=root / "artifacts"),
            )

            record = service.submit(
                {
                    "parse_mode": "ocr",
                    "file_base64": "QUJD",
                    "media_type": "image/png",
                    "filename": "sample.png",
                }
            ).metadata

            self.assertEqual(record["status"], "succeeded")
            self.assertTrue(record["ingest_id"].startswith("doc-ingest-"))
            self.assertTrue(record["artifact_id"].startswith("doc-artifact-"))
            self.assertEqual(record["warnings"], ["minor"])
            self.assertEqual(runtime.calls[0][0], "document.ocr.extract")

            result = service.get_result(record["ingest_id"])
            self.assertEqual(result["payload"]["text"], "hello")
            self.assertNotIn("raw", result["payload"])
            self.assertEqual(service.list()[0]["ingest_id"], record["ingest_id"])

    def test_submit_layout_forwards_options_and_persists_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = FakeCapabilityRuntime(
                {
                    "document.layout.parse": {
                        "ok": True,
                        "provider": "paddleocr",
                        "result": {
                            "markdown": "# Doc",
                            "elements": [],
                            "tables": [{"rows": 2}],
                            "warnings": [],
                        },
                    }
                }
            )
            service = DocumentIngestionService(
                root_dir=root / "ingestions",
                capability_runtime=runtime,
                artifact_service=DocumentArtifactService(root_dir=root / "artifacts"),
            )

            record = service.submit(
                {
                    "parse_mode": "layout",
                    "file_base64": "QUJD",
                    "media_type": "application/pdf",
                    "filename": "layout.pdf",
                    "output_format": "json",
                    "include_tables": False,
                    "include_layout": False,
                    "max_pages": 3,
                }
            ).metadata

            self.assertEqual(record["status"], "succeeded")
            _, payload = runtime.calls[0]
            self.assertEqual(payload["output_format"], "json")
            self.assertFalse(payload["include_tables"])
            self.assertFalse(payload["include_layout"])
            self.assertEqual(payload["max_pages"], 3)

    def test_vlm_async_non_terminal_records_provider_job(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = FakeCapabilityRuntime(
                {
                    "document.vlm.parse.async": {
                        "ok": True,
                        "provider": "document_vlm_provider",
                        "result": {
                            "job_id": "job-1",
                            "status": "running",
                            "progress": 0.4,
                            "warnings": [],
                        },
                    }
                }
            )
            service = DocumentIngestionService(
                root_dir=root / "ingestions",
                capability_runtime=runtime,
                artifact_service=DocumentArtifactService(root_dir=root / "artifacts"),
            )

            record = service.submit(
                {
                    "parse_mode": "vlm_async",
                    "file_base64": "QUJD",
                    "media_type": "application/pdf",
                    "filename": "doc.pdf",
                    "task": "summarize",
                }
            ).metadata

            self.assertEqual(record["status"], "running")
            self.assertEqual(record["provider_job"]["job_id"], "job-1")
            self.assertEqual(record["artifact_id"], "")

    def test_provider_failure_is_recorded_as_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = FakeCapabilityRuntime(
                {
                    "document.ocr.extract": {
                        "ok": False,
                        "error": {"code": "CAPABILITY_PROVIDER_UNREACHABLE", "message": "down"},
                    }
                }
            )
            service = DocumentIngestionService(
                root_dir=root / "ingestions",
                capability_runtime=runtime,
                artifact_service=DocumentArtifactService(root_dir=root / "artifacts"),
            )

            record = service.submit(
                {
                    "parse_mode": "ocr",
                    "file_base64": "QUJD",
                    "media_type": "image/png",
                    "filename": "sample.png",
                }
            ).metadata

            self.assertEqual(record["status"], "failed")
            self.assertEqual(record["error"]["code"], "DOCUMENT_INGEST_PROVIDER_UNAVAILABLE")
            self.assertEqual(record["error"]["provider_error"]["code"], "CAPABILITY_PROVIDER_UNREACHABLE")

    def test_missing_ingestion_raises_structured_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = DocumentIngestionService(root_dir=Path(tmp), capability_runtime=FakeCapabilityRuntime())

            with self.assertRaises(DocumentIngestionNotFound):
                service.get("missing")


class DocumentIngestionRouterTests(unittest.TestCase):
    def test_router_submit_read_result_and_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            previous = service_module._document_ingestion_service
            service_module._document_ingestion_service = DocumentIngestionService(
                root_dir=root / "ingestions",
                capability_runtime=FakeCapabilityRuntime(
                    {
                        "document.ocr.extract": {
                            "ok": True,
                            "provider": "paddleocr",
                            "result": {"text": "router text", "pages": [], "blocks": [], "warnings": []},
                        }
                    }
                ),
                artifact_service=DocumentArtifactService(root_dir=root / "artifacts"),
            )
            try:
                app = FastAPI()
                app.include_router(document_ingestions.router)
                client = TestClient(app)

                created = client.post(
                    "/api/document-ingestions",
                    json={
                        "parse_mode": "ocr",
                        "file_base64": "QUJD",
                        "media_type": "image/png",
                        "filename": "sample.png",
                    },
                )
                self.assertEqual(created.status_code, 200)
                ingest_id = created.json()["ingestion"]["ingest_id"]
                self.assertTrue(created.json()["ingestion"]["artifact_id"].startswith("doc-artifact-"))

                fetched = client.get(f"/api/document-ingestions/{ingest_id}")
                self.assertEqual(fetched.status_code, 200)
                self.assertEqual(fetched.json()["ingestion"]["status"], "succeeded")

                result = client.get(f"/api/document-ingestions/{ingest_id}/result")
                self.assertEqual(result.status_code, 200)
                self.assertEqual(result.json()["payload"]["text"], "router text")

                missing = client.get("/api/document-ingestions/missing")
                self.assertEqual(missing.status_code, 404)
                self.assertEqual(missing.json()["error"]["code"], "DOCUMENT_INGEST_NOT_FOUND")
            finally:
                service_module._document_ingestion_service = previous


if __name__ == "__main__":
    unittest.main()
