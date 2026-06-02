import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routers import document_artifacts
from backend.services import document_artifact_service as service_module
from backend.services.document_artifact_service import DocumentArtifactNotFound, DocumentArtifactService


class DocumentArtifactServiceTests(unittest.TestCase):
    def test_persist_read_and_list_compact_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = DocumentArtifactService(root_dir=Path(tmp))

            persisted = service.persist(
                {
                    "source_filename": "sample.pdf",
                    "media_type": "application/pdf",
                    "capability_id": "document.layout.parse",
                    "provider": "paddleocr",
                    "result": {
                        "markdown": "# Title",
                        "tables": [{"rows": 2}],
                        "warnings": ["minor"],
                        "raw": {"huge": True},
                    },
                }
            )

            metadata = persisted.metadata
            self.assertTrue(metadata["artifact_id"].startswith("doc-artifact-"))
            self.assertEqual(metadata["artifact_type"], "document.layout")
            self.assertEqual(metadata["source_filename"], "sample.pdf")
            self.assertEqual(metadata["warnings"], ["minor"])
            self.assertFalse(metadata["raw_included"])
            self.assertNotIn("raw", persisted.payload)

            loaded = service.get(metadata["artifact_id"])
            self.assertEqual(loaded.metadata["content_hash"], metadata["content_hash"])
            self.assertEqual(loaded.payload["markdown"], "# Title")
            self.assertEqual(service.list()[0]["artifact_id"], metadata["artifact_id"])

    def test_include_raw_is_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = DocumentArtifactService(root_dir=Path(tmp))

            persisted = service.persist(
                {
                    "capability_id": "document.ocr.extract",
                    "provider": "paddleocr",
                    "include_raw": True,
                    "result": {
                        "text": "hello",
                        "warnings": [],
                        "raw": {"kept": True},
                    },
                }
            )

            self.assertTrue(persisted.metadata["raw_included"])
            self.assertEqual(persisted.payload["raw"]["kept"], True)

    def test_missing_artifact_raises_structured_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = DocumentArtifactService(root_dir=Path(tmp))

            with self.assertRaises(DocumentArtifactNotFound):
                service.get("missing")


class DocumentArtifactRouterTests(unittest.TestCase):
    def test_router_persist_read_and_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            previous = service_module._document_artifact_service
            service_module._document_artifact_service = DocumentArtifactService(root_dir=Path(tmp))
            try:
                app = FastAPI()
                app.include_router(document_artifacts.router)
                client = TestClient(app)

                created = client.post(
                    "/api/document-artifacts",
                    json={
                        "capability_id": "document.vlm.parse",
                        "provider": "document_vlm_provider",
                        "result": {"summary": "semantic summary", "raw": {"drop": True}},
                    },
                )
                self.assertEqual(created.status_code, 200)
                artifact_id = created.json()["artifact"]["artifact_id"]

                fetched = client.get(f"/api/document-artifacts/{artifact_id}")
                self.assertEqual(fetched.status_code, 200)
                self.assertEqual(fetched.json()["payload"]["summary"], "semantic summary")
                self.assertNotIn("raw", fetched.json()["payload"])

                listing = client.get("/api/document-artifacts")
                self.assertEqual(listing.status_code, 200)
                self.assertEqual(listing.json()["artifacts"][0]["artifact_id"], artifact_id)

                missing = client.get("/api/document-artifacts/missing")
                self.assertEqual(missing.status_code, 404)
                self.assertEqual(missing.json()["error"]["code"], "DOCUMENT_ARTIFACT_NOT_FOUND")
            finally:
                service_module._document_artifact_service = previous


if __name__ == "__main__":
    unittest.main()
