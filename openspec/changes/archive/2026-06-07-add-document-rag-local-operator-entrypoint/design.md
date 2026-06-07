# Design: Document RAG Local Operator Entrypoint

## Backend

Add a small orchestration service:

```text
backend/capability_runtime/document_rag_local_operator_entrypoint.py
```

It composes:

- `export_document_rag_local_readiness`
- `export_document_rag_upload_to_use_loop`

It does not duplicate OCR parsing, provider ingestion, or corpus trial logic.

## API

Add router:

```text
backend/routers/document_rag_local_trials.py
```

Endpoints:

```text
POST /api/document-rag/local-trials/readiness
POST /api/document-rag/local-trials
```

### Readiness Payload

- `ocr_base_url`
- `ocr_profile`
- `ocr_timeout_seconds`
- `provider_base_url`
- `source_id`
- `knowledge_provider_repo`
- `provider_python`
- `timeout_seconds`
- `output_dir`

### Trial Payload

All readiness fields plus:

- `document_path`
- `parse_mode`
- `title`
- `query`
- `top_k`
- `max_pages`
- `handoff_only`
- `allow_review_readiness`

## Decision Flow

```text
local trial request
  -> run readiness
  -> if readiness blocked: return blocked, upload_to_use not_run
  -> if readiness review and allow_review_readiness=false: return review, upload_to_use not_run
  -> otherwise run upload-to-use loop
  -> return combined decision and report paths
```

## Frontend

Add a compact card to `CapabilityProviderDiagnosticsPanel.vue`:

- document path
- parse mode
- source id
- OCR profile
- OCR timeout
- readiness button
- local trial button
- result summary and raw JSON details

This keeps the entrypoint in Settings diagnostics rather than creating a new product surface.

## Boundaries

- The API remains local operator tooling.
- It does not start services.
- It does not mutate chat defaults or agent bindings.
- It does not write governance state.
- It does not execute GraphRAG.
