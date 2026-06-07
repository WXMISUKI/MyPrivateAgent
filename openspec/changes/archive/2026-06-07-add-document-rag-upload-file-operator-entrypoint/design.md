# Design: Document RAG Upload File Operator Entrypoint

## Backend

Extend:

```text
backend/capability_runtime/document_rag_local_operator_entrypoint.py
backend/routers/document_rag_local_trials.py
```

The router accepts upload payloads, materializes uploaded bytes into a controlled local directory, and then calls the existing local trial entrypoint with the materialized `document_path`.

## Upload Materialization

Default directory:

```text
.myagent/document-rag-operator-uploads
```

The materialized filename is sanitized and prefixed with a short content hash:

```text
<sha256-12>-<safe-filename>
```

The file is retained so generated reports can point to a stable local input path. This is not a long-term document management feature; retention cleanup is left for a later operational slice if needed.

## API Payload

`POST /api/document-rag/local-trials` keeps the existing path mode:

```json
{
  "document_path": "D:/docs/company.pdf"
}
```

It also accepts upload mode:

```json
{
  "file_base64": "...",
  "filename": "company.pdf",
  "media_type": "application/pdf"
}
```

If both are supplied, upload mode wins because it represents the browser-selected file.

## Decision Flow

```text
local trial request
  -> if file_base64 present: materialize upload to local operator directory
  -> else use document_path
  -> run readiness
  -> if readiness blocked: return blocked, upload_to_use not_run
  -> if readiness review and allow_review_readiness=false: return review, upload_to_use not_run
  -> otherwise run existing upload-to-use loop
  -> return combined decision, report paths, and upload metadata
```

## Frontend

Extend `CapabilityProviderDiagnosticsPanel.vue`:

- add a file input to the existing local document RAG card
- keep the path input as advanced/debug fallback
- build `file_base64`, `filename`, and `media_type` with the existing file helpers
- display the selected filename and materialized upload path when returned

## Boundaries

- The entrypoint remains explicit local tooling.
- It does not start services.
- It does not mutate chat defaults or agent bindings.
- It does not write governance state.
- It does not execute GraphRAG.
