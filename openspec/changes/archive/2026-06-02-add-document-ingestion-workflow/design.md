## Design Summary

Introduce a local document ingestion workflow that coordinates existing document capabilities and artifact persistence.

The workflow is intentionally control-plane focused:

- MyPrivateAgent accepts a document payload and parse policy.
- MyPrivateAgent invokes the already registered capability provider.
- Successful compact results are persisted as document artifacts.
- Ingestion status and artifact references are persisted locally.

External provider services still own heavy parsing.

## Parse Modes

Supported parse modes:

- `ocr`: invokes `document.ocr.extract`
- `layout`: invokes `document.layout.parse`
- `vlm_async`: invokes `document.vlm.parse.async`

`vlm_async` support is minimal for this change: submit to the async capability and persist terminal results only when the provider returns `status=succeeded` with a result in the same request. Non-terminal jobs are stored with provider job metadata and can be queried through ingestion status.

## Storage Layout

Default root:

```text
<LOCAL_DATA_DIR>/document_ingestions/
  index.json
  <ingest_id>/
    metadata.json
```

Metadata contains:

- `ingest_id`
- `status`
- `parse_mode`
- `capability_id`
- `provider`
- `source_filename`
- `media_type`
- `created_at`
- `updated_at`
- `artifact_id`
- `artifact`
- `provider_job`
- `warnings`
- `error`
- `request`

The original source binary is not stored.

## API Shape

```http
POST /api/document-ingestions
GET  /api/document-ingestions
GET  /api/document-ingestions/{ingest_id}
GET  /api/document-ingestions/{ingest_id}/result
```

Submit request:

```json
{
  "file_base64": "...",
  "media_type": "application/pdf",
  "filename": "sample.pdf",
  "parse_mode": "layout",
  "output_format": "markdown",
  "include_tables": true,
  "include_layout": true,
  "max_pages": 10
}
```

Submit response:

```json
{
  "ok": true,
  "ingestion": {
    "ingest_id": "doc-ingest-...",
    "status": "succeeded",
    "parse_mode": "layout",
    "artifact_id": "doc-artifact-..."
  }
}
```

## Status Vocabulary

- `queued`
- `running`
- `succeeded`
- `failed`

The first implementation runs synchronously inside the request and records terminal state before returning. The status vocabulary leaves room for future async OCR/Layout jobs.

## Error Codes

- `DOCUMENT_INGEST_INVALID_INPUT`
- `DOCUMENT_INGEST_NOT_FOUND`
- `DOCUMENT_INGEST_PROVIDER_UNAVAILABLE`
- `DOCUMENT_INGEST_ARTIFACT_PERSIST_FAILED`

## Frontend Boundary

The diagnostics panel adds a small document ingestion test section. It should not become a document management page.

The UI displays:

- `ingest_id`
- `status`
- `artifact_id`
- warnings
- structured errors
- raw ingestion JSON for debugging

## Future Work

- Durable async OCR/Layout ingestion jobs.
- Knowledge/RAG handoff through `knowledge.document.ingest`.
- Binary source storage policy.
- Production object storage adapter.
- Full document management and review UI.
