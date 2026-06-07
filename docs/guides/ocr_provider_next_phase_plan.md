# OCR Provider Next Phase Plan

## Current State

MyPrivateAgent has completed the first external document capability ladder:

- `document.ocr.extract`: baseline OCR for image/PDF text extraction.
- `document.layout.parse`: PP-StructureV3 layout/table/markdown parsing.
- `document.vlm.parse`: synchronous semantic document understanding contract.
- `document.vlm.parse.async`: async submit/status contract validated through a local wrapper provider.

Validated local providers:

- OCR: `http://127.0.0.1:8080/ocr`
- Layout: `http://127.0.0.1:8081/layout-parsing`
- VLM async wrapper: `http://127.0.0.1:8082/api/vlm/jobs`

The current implementation is strong enough for local debugging and capability diagnostics. The next phase should move from "can call provider" to "can safely consume document intelligence in product workflows."

## Priority 1: Artifact And Provenance Contract

Status: implemented in OpenSpec change `add-document-artifact-contract`.

Problem:

OCR/Layout/VLM outputs currently return useful text, blocks, markdown, and raw provider evidence, but the project does not yet have a durable artifact contract for source files, page images, markdown snapshots, table outputs, or traceable OCR evidence.

Recommended next capability slice:

```text
document.artifact.persist
document.artifact.get
```

Minimum scope:

- Persist compact OCR/Layout/VLM outputs under a local artifact root.
- Store metadata:
  - `artifact_id`
  - `source_filename`
  - `media_type`
  - `capability_id`
  - `provider`
  - `created_at`
  - `content_hash`
  - `summary`
  - `warnings`
- Keep large raw provider payloads optional and disabled by default.
- Return artifact references from diagnostics and future ingestion workflows.

Why first:

Without artifacts, downstream RAG, domain agents, and audits cannot distinguish stable evidence from one-off test output.

## Priority 2: Document Ingestion Workflow

Status: implemented in OpenSpec change `add-document-ingestion-workflow`.

Problem:

The diagnostics panel can test capabilities, but there is not yet a formal user/business workflow for "upload document -> OCR/Layout -> review -> persist -> hand off to knowledge/RAG."

Recommended workflow:

```text
document.ingest.submit
document.ingest.status
document.ingest.result
```

Minimum scope:

- Upload image/PDF through MyPrivateAgent control plane.
- Choose parse mode:
  - OCR only
  - Layout markdown
  - VLM async summary
- Persist output artifact references.
- Expose status and warnings.

Boundary:

The heavy parsing still runs in external providers. MyPrivateAgent owns orchestration, policy, artifact references, and audit metadata.

Implementation notes:

- Backend exposes `POST /api/document-ingestions`, `GET /api/document-ingestions`, `GET /api/document-ingestions/{ingest_id}`, and `GET /api/document-ingestions/{ingest_id}/result`.
- Supported parse modes are `ocr`, `layout`, and `vlm_async`.
- Successful OCR/Layout outputs are persisted through the document artifact contract.
- Non-terminal VLM async responses record provider job metadata and do not fabricate artifact ids.
- The diagnostics panel now includes a minimal document ingestion test area.

## Priority 3: Quality And Evaluation Dataset

Problem:

Current acceptance uses three samples. That is enough for smoke, but not enough for regression confidence.

Recommended next assets:

- `sample-clean-text`
- `sample-table`
- `sample-contract`
- `sample-multipage-pdf`
- `sample-mixed-cn-en`
- `sample-low-quality-scan`

Acceptance metrics:

- OCR text length non-empty.
- Page count matches expectation.
- Layout markdown non-empty.
- Tables detected when expected.
- Warnings captured when expected.
- VLM async reaches terminal status within threshold.

Recommended report shape:

```json
{
  "sample_id": "sample-table",
  "capability_id": "document.layout.parse",
  "ok": true,
  "latency_ms": 8520,
  "text_length": 155,
  "markdown_length": 813,
  "table_count": 1,
  "warning_count": 0
}
```

## Priority 4: Async OCR/Layout Jobs

Problem:

OCR and Layout are still synchronous from MyPrivateAgent's perspective. This is fine for small files, but large PDFs and batch processing should not remain sync-only.

Recommended capability ids:

```text
document.ocr.extract.async
document.layout.parse.async
```

Minimum scope:

- Mirror VLM async semantics:
  - `operation=submit`
  - `operation=status`
  - `job_id`
  - `queued/running/succeeded/failed/expired`
- Reuse the same local wrapper provider pattern.
- Keep sync capabilities for small files.

When to implement:

After artifact contract is in place, because async jobs should return artifact refs rather than huge inline raw payloads.

## Priority 5: Knowledge/RAG Handoff

Status: local upload-to-use trial implemented in OpenSpec change `add-document-rag-upload-to-use-loop`.

Problem:

OCR/Layout output is not yet connected to knowledge ingestion or agent tools.

Recommended handoff contract:

```text
knowledge.document.ingest
```

Input:

- `artifact_id`
- `source_type`
- `parse_mode`
- `metadata`

Output:

- `document_id`
- `source_id`
- `chunks`
- `citations`
- `warnings`

Boundary:

The knowledge provider owns chunking, embedding, rerank, and indexing. MyPrivateAgent only passes artifact references and receives ingestion status.

Current local shape:

- `scripts/export_document_rag_upload_to_use_loop.py` reuses `DocumentIngestionService` for OCR/Layout parsing.
- The loop converts the persisted document artifact into a unifiedKnowledgeRAG parser artifact JSON.
- The loop can invoke the provider repo ingestion command and then reuse the existing local knowledge provider corpus trial.
- This remains explicit operator tooling; it does not enable default `/api/chat` retrieval injection, source binding, answer policy, memory/audit writes, or GraphRAG.
- `scripts/export_document_rag_local_readiness.py` can be run before the upload-to-use loop to verify OCR provider health, CPU/GPU profile, large-PDF timeout posture, unifiedKnowledgeRAG health, source visibility, provider repo script, and `GRAPHRAG` Python command readiness.

Next productization trigger:

- Promote `knowledge.document.ingest` only when the provider exposes a stable HTTP ingestion API and the local command bridge is no longer enough for day-to-day use.

## Priority 6: Provider Packaging And Startup Reliability

Problem:

The local setup currently requires multiple commands and ports.

Recommended improvements:

- Add a documented startup matrix for:
  - OCR on 8080
  - Layout on 8081
  - VLM async wrapper on 8082
  - MyPrivateAgent on 8000
- Add provider doctor checks:
  - port reachable
  - `/health` JSON shape valid
  - expected route exists
  - sample invoke works
- Keep this as scripts/docs first; avoid Dockerizing until the contract stabilizes.

## Recommended Next OpenSpec Change

Best next slice:

```text
add-document-artifact-contract
```

Why:

- It is the smallest step that makes OCR/Layout/VLM outputs reusable outside diagnostics.
- It reduces risk before adding async OCR/Layout jobs.
- It creates the foundation for RAG ingestion, audit, review, and future domain-agent workflows.

Proposed tasks:

1. Add artifact contract spec for document capability outputs.
2. Implement local artifact metadata store.
3. Add compact artifact persistence helper for OCR/Layout/VLM results.
4. Update diagnostics to optionally persist successful results.
5. Add focused tests for artifact id, metadata, and raw-payload exclusion.

Minimal verification:

```bash
python -m pytest tests/agent_framework/test_document_artifact_service.py tests/agent_framework/test_capability_http_provider.py tests/agent_framework/test_document_vlm_async_wrapper_provider.py -q
npm run test -- src/components/__tests__/CapabilityProviderDiagnosticsPanel.test.js
```

Implementation notes:

- Backend exposes `POST /api/document-artifacts`, `GET /api/document-artifacts`, and `GET /api/document-artifacts/{artifact_id}`.
- Local payload storage lives under `<LOCAL_DATA_DIR>/document_artifacts`.
- Capability diagnostics can persist successful OCR/Layout/VLM results on demand and display `artifact_id`.
- Raw provider payloads remain excluded unless `include_raw=true`.

## Explicit Non-goals

- Do not put PaddleOCR/PaddleOCR-VL dependencies inside MyPrivateAgent backend.
- Do not make OCR automatic in `/api/chat`.
- Do not persist raw provider payloads by default.
- Do not build full document management UI yet.
- Do not connect to RAG ingestion before artifact provenance is stable.
