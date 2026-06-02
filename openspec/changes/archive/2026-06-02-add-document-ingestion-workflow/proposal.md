## Why

MyPrivateAgent can now invoke external document providers and persist compact OCR/Layout/VLM artifacts, but these operations are still exposed mainly through diagnostics.

The next product-facing control-plane step is a formal document ingestion workflow:

```text
upload file -> choose parse mode -> invoke OCR/Layout/VLM -> persist artifact -> return ingest job/result
```

This lets users and future agent workflows create a durable document intelligence result without depending on diagnostics-only UI behavior.

## What Changes

- Add a lightweight document ingestion contract with submit/status/result APIs.
- Add local ingestion metadata persistence under `LOCAL_DATA_DIR/document_ingestions`.
- Orchestrate existing capability runtime invocations for:
  - `document.ocr.extract`
  - `document.layout.parse`
  - `document.vlm.parse.async`
- Persist successful provider outputs through the existing document artifact service.
- Add a minimal frontend diagnostics ingestion section for local testing.
- Keep heavy OCR/Layout/VLM parsing in external providers.

## Impact

- Backend:
  - new document ingestion service
  - new API router endpoints
  - local ingestion metadata files
  - reuse existing capability runtime and artifact service
- Frontend:
  - new ingestion API wrapper
  - minimal diagnostics test section
- Docs/spec:
  - canonical ingestion workflow contract and usage guide

## Non-goals

- No RAG/knowledge ingestion in this change.
- No automatic `/api/chat` document ingestion.
- No PaddleOCR/PaddleOCR-VL dependency inside MyPrivateAgent.
- No source binary persistence beyond transient request payload handling.
- No full document management UI.
