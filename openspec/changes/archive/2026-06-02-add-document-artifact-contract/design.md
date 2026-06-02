## Design Summary

Introduce a local document artifact store for compact provider-neutral outputs from:

- `document.ocr.extract`
- `document.layout.parse`
- `document.vlm.parse`
- `document.vlm.parse.async`

The store persists metadata and compact payload separately so future ingestion/review flows can reference `artifact_id` without keeping huge provider raw JSON in memory or documents.

## Storage Layout

Default root:

```text
<LOCAL_DATA_DIR>/document_artifacts/
  index.json
  <artifact_id>/
    metadata.json
    payload.json
```

`metadata.json` contains:

- `artifact_id`
- `artifact_type`
- `source_filename`
- `media_type`
- `capability_id`
- `provider`
- `created_at`
- `content_hash`
- `summary`
- `warnings`
- `payload_path`
- `raw_included`

`payload.json` contains compact output:

- OCR: `text/pages/blocks/tables/artifacts/warnings`
- Layout: `markdown/elements/tables/pages/artifacts/warnings`
- VLM: `summary/sections/entities/answers/evidence/warnings`
- Async VLM: normalized final `result` fields

## API Shape

```http
POST /api/document-artifacts
GET  /api/document-artifacts/{artifact_id}
GET  /api/document-artifacts
```

Persist request:

```json
{
  "source_filename": "sample.pdf",
  "media_type": "application/pdf",
  "capability_id": "document.layout.parse",
  "provider": "paddleocr",
  "result": {},
  "include_raw": false
}
```

Persist response:

```json
{
  "ok": true,
  "artifact": {
    "artifact_id": "doc-artifact-...",
    "artifact_type": "document.layout",
    "summary": "markdown preview",
    "warnings": []
  }
}
```

## Compaction Rules

- Drop `raw` unless `include_raw=true`.
- Compute `content_hash` from compact payload.
- Derive a short summary from text/markdown/summary fields.
- Preserve warnings.
- Keep artifact metadata provider-neutral.

## Frontend Boundary

Capability diagnostics can persist successful results on demand. It should not auto-persist every test result.

The UI should display the returned `artifact_id` so users can reference it in future ingestion or debugging workflows.

## Future Work

- `document.ingest.*` workflow
- knowledge provider handoff
- source binary storage policy
- artifact retention and deletion
- production object storage adapter
