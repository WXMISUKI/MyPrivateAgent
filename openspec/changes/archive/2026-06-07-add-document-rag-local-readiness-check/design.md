# Design: Document RAG Local Readiness Check

## Approach

Add a side-effect-free capability runtime helper and CLI exporter:

```text
scripts/export_document_rag_local_readiness.py
  -> backend.capability_runtime.document_rag_local_readiness
```

The checker performs lightweight local probes only. It does not reuse `DocumentIngestionService` because the purpose is to fail early before invoking OCR or uploading real files.

## Checks

### OCR Provider

- Probe `GET /health` for the configured OCR provider base URL.
- Record status, endpoint, error if unreachable, and timeout.
- Record operator-supplied OCR profile:
  - `cpu`
  - `gpu`
  - `unknown`
- Record timeout recommendation:
  - large PDFs should use a higher OCR timeout than the current 30 second local default.

### Knowledge Provider

- Probe `GET /health`.
- Probe `GET /api/rag/sources`.
- If a source id is configured, report whether the source is visible.

### Provider Command

- Check provider repo path exists.
- Check `scripts/export_parser_artifact_local_ingestion_loop.py` exists in the provider repo.
- Check configured provider Python command can be invoked with `--version` or an equivalent low-cost command.

## Decision Rules

- `blocked`: any required service is unreachable, provider repo is missing, ingestion script is missing, or provider Python command cannot run.
- `review`: required checks pass, but source visibility is missing, OCR profile is unknown, or timeout/profile posture suggests operator review.
- `go`: required checks pass, source is visible when configured, and no review warnings remain.

## Output

The exporter writes:

- `docs/integration/document-rag-local-readiness/document-rag-local-readiness.json`
- `docs/integration/document-rag-local-readiness/document-rag-local-readiness.md`

## Boundaries

This checker is local operator tooling. It must not:

- parse documents
- start services
- mutate provider data
- mutate MyPrivateAgent runtime data
- promote retrieval defaults
- execute GraphRAG
