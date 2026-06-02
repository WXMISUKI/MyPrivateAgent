# Document Ingestion Workflow Guide

This guide documents the control-plane workflow for document ingestion in MyPrivateAgent.

## Purpose

The workflow upgrades document capability usage from diagnostics-only testing to a formal ingestion job:

```text
upload file -> choose parse mode -> invoke OCR/Layout/VLM -> persist artifact -> return ingest job/result
```

MyPrivateAgent owns orchestration, policy, status, artifact references, and audit-friendly metadata. External providers still own heavy parsing.

## Supported Parse Modes

- `ocr`: invokes `document.ocr.extract`
- `layout`: invokes `document.layout.parse`
- `vlm_async`: invokes `document.vlm.parse.async`

The first implementation runs OCR/Layout synchronously inside the request. `vlm_async` records provider job metadata for non-terminal jobs and persists an artifact only when a terminal successful result is already available.

## API

Submit ingestion:

```http
POST /api/document-ingestions
```

```json
{
  "parse_mode": "layout",
  "file_base64": "...",
  "media_type": "application/pdf",
  "filename": "sample.pdf",
  "output_format": "markdown",
  "include_tables": true,
  "include_layout": true,
  "max_pages": 10
}
```

Read status:

```http
GET /api/document-ingestions/{ingest_id}
```

Read result:

```http
GET /api/document-ingestions/{ingest_id}/result
```

List recent ingestions:

```http
GET /api/document-ingestions?limit=50
```

## Response Shape

Successful terminal ingestion:

```json
{
  "ok": true,
  "ingestion": {
    "ingest_id": "doc-ingest-...",
    "status": "succeeded",
    "parse_mode": "layout",
    "capability_id": "document.layout.parse",
    "provider": "paddleocr",
    "artifact_id": "doc-artifact-...",
    "warnings": []
  }
}
```

Non-terminal VLM async ingestion:

```json
{
  "ok": true,
  "ingestion": {
    "ingest_id": "doc-ingest-...",
    "status": "running",
    "parse_mode": "vlm_async",
    "provider_job": {
      "job_id": "job-...",
      "status": "running",
      "progress": 0.4
    },
    "artifact_id": ""
  }
}
```

Structured errors use stable codes:

- `DOCUMENT_INGEST_INVALID_INPUT`
- `DOCUMENT_INGEST_NOT_FOUND`
- `DOCUMENT_INGEST_PROVIDER_UNAVAILABLE`
- `DOCUMENT_INGEST_ARTIFACT_PERSIST_FAILED`

## Diagnostics Usage

Open the capability diagnostics panel and use `文档 Ingestion 测试`:

1. Select an image or PDF file.
2. Choose `ocr`, `layout`, or `vlm_async`.
3. Fill optional mode-specific fields.
4. Submit ingestion.
5. Read `ingest_id`, `status`, `artifact_id`, warnings, and raw JSON.

## Boundary

This workflow does not store source binaries and does not push artifacts into RAG yet. Future stages should use `artifact_id` as the handoff input for `knowledge.document.ingest`.
