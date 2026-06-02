# Document Artifact Contract Guide

This guide documents the local artifact contract used to persist compact OCR, layout, and document VLM results.

## Purpose

Document capabilities return useful transient results during diagnostics:

- OCR text, pages, blocks, and confidence data.
- Layout markdown, elements, tables, and pages.
- VLM summaries, sections, answers, entities, and evidence.

The artifact contract turns those successful results into stable references for later review, audit, and future knowledge/RAG handoff.

## Storage

Artifacts are stored under:

```text
<LOCAL_DATA_DIR>/document_artifacts/
  index.json
  <artifact_id>/
    metadata.json
    payload.json
```

`metadata.json` contains provider-neutral provenance:

```json
{
  "artifact_id": "doc-artifact-...",
  "artifact_type": "document.layout",
  "source_filename": "sample.pdf",
  "media_type": "application/pdf",
  "capability_id": "document.layout.parse",
  "provider": "paddleocr",
  "created_at": "2026-06-02T00:00:00+00:00",
  "content_hash": "...",
  "summary": "short preview",
  "warnings": [],
  "payload_path": "doc-artifact-.../payload.json",
  "raw_included": false
}
```

`payload.json` stores compact semantic output. Raw provider payloads are excluded by default.

## API

Persist a successful capability result:

```http
POST /api/document-artifacts
```

```json
{
  "source_filename": "sample.pdf",
  "media_type": "application/pdf",
  "capability_id": "document.layout.parse",
  "provider": "paddleocr",
  "include_raw": false,
  "result": {
    "markdown": "# Title",
    "elements": [],
    "tables": [],
    "pages": [],
    "warnings": []
  }
}
```

Read an artifact:

```http
GET /api/document-artifacts/{artifact_id}
```

List recent artifacts:

```http
GET /api/document-artifacts?limit=50
```

Unknown artifacts return:

```json
{
  "ok": false,
  "error": {
    "code": "DOCUMENT_ARTIFACT_NOT_FOUND",
    "message": "Document artifact not found: doc-artifact-missing",
    "artifact_id": "doc-artifact-missing"
  }
}
```

## Diagnostics Usage

In the frontend capability diagnostics panel:

1. Run OCR, Layout, VLM, or completed async VLM.
2. After a successful result, click `保存 Artifact`.
3. Copy the returned `artifact_id` for future ingestion or debugging.

The diagnostics panel does not auto-persist results. This keeps local storage deliberate and avoids saving large or accidental test output.

## Boundary

This contract does not persist the original binary source file and does not connect to RAG ingestion yet. Future stages should pass `artifact_id` into a document ingestion workflow after the artifact provenance contract is stable.
