## Why

MyPrivateAgent can already call PaddleOCR document capabilities and persist document artifacts, while unifiedKnowledgeRAG can ingest a normalized parser artifact into its local RAG loop. The missing caller-side slice is a small, repeatable local flow that starts from a real user document in MyPrivateAgent and ends with a provider-visible RAG source that can be queried.

## What Changes

- Add a MyPrivateAgent local document RAG upload-to-use loop.
- The loop reads a local document file, submits it through the existing document ingestion workflow, converts the persisted artifact into a normalized parser artifact handoff, invokes the local unifiedKnowledgeRAG parser-artifact ingestion command, and verifies the resulting source through the existing local knowledge provider corpus trial.
- Add a CLI exporter that writes JSON/Markdown reports with `go / review / blocked` decisions.
- Keep the implementation explicit and local-first because unifiedKnowledgeRAG does not yet expose a stable HTTP `knowledge.document.ingest` API.
- Preserve boundaries: no default `/api/chat` RAG injection, no source-to-agent binding, no GraphRAG, no background job platform, no frontend product workflow in this slice.

## Capabilities

### New Capabilities
- `document-rag-upload-to-use-loop`: Covers the local MyPrivateAgent document-to-RAG trial loop from file ingestion to provider-side RAG usability verification.

### Modified Capabilities
- `unified-knowledge-capability-runtime`: Clarifies that MyPrivateAgent may use a local document RAG upload-to-use loop as a caller-side trial without promoting default chat retrieval or GraphRAG execution.

## Impact

- Affected code:
  - new backend capability-runtime service for document RAG upload-to-use loop
  - new CLI exporter under `scripts/`
  - focused tests using fake document ingestion, command runner, and corpus trial dependencies
- Affected docs:
  - local report artifacts under `docs/integration/document-rag-upload-to-use-loop/`
  - architecture note update for the new local trial loop
- External systems:
  - optional local PaddleOCR provider through the existing `DocumentIngestionService`
  - optional local unifiedKnowledgeRAG repo command path
  - optional local unifiedKnowledgeRAG HTTP provider verification at `http://127.0.0.1:8020`
- No breaking API changes.
