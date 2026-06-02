## Why

OCR/Layout/VLM capabilities can now return useful text, markdown, tables, semantic summaries, and raw provider evidence, but the results are still one-off responses from diagnostics or smoke scripts.

Without a durable artifact/provenance contract, downstream RAG ingestion, domain agents, audit trails, and review workflows cannot safely distinguish stable document evidence from transient test output.

## What Changes

- Add a lightweight document artifact contract for compact OCR/Layout/VLM outputs.
- Add local artifact persistence under `LOCAL_DATA_DIR/document_artifacts`.
- Add API endpoints to persist and read document artifacts.
- Keep raw provider payloads excluded by default.
- Allow diagnostics users to persist successful OCR/Layout/VLM results for later handoff.

## Impact

- Backend:
  - new document artifact service
  - new API router endpoints
  - compact metadata and payload files
- Frontend:
  - optional persist action in capability diagnostics result view
- Docs/spec:
  - canonical artifact contract and usage guide

## Non-goals

- No RAG/knowledge ingestion in this change.
- No full document management UI.
- No binary source file upload persistence.
- No raw provider payload persistence by default.
- No PaddleOCR/PaddleOCR-VL dependency inside MyPrivateAgent.
