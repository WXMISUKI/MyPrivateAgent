## 1. Spec

- [x] 1.1 Create OpenSpec proposal and design for document ingestion workflow.
- [x] 1.2 Add `unified-capability-runtime` requirement delta for ingestion submit/status/result.
- [x] 1.3 Define parse mode, status vocabulary, artifact handoff, and structured errors.

## 2. Backend

- [x] 2.1 Add document ingestion service with local metadata persistence.
- [x] 2.2 Add ingestion orchestration for OCR parse mode.
- [x] 2.3 Add ingestion orchestration for Layout parse mode.
- [x] 2.4 Add VLM async ingestion support with provider job metadata and terminal artifact persistence.
- [x] 2.5 Persist successful outputs through `DocumentArtifactService`.
- [x] 2.6 Add document ingestion API router and register it.
- [x] 2.7 Add structured input, not-found, provider, and artifact persistence errors.

## 3. Frontend

- [x] 3.1 Add document ingestion API wrapper.
- [x] 3.2 Add minimal ingestion test section in diagnostics panel.
- [x] 3.3 Display `ingest_id`, `status`, `artifact_id`, warnings, raw JSON, and structured errors.

## 4. Docs

- [x] 4.1 Add document ingestion workflow usage guide and API examples.
- [x] 4.2 Update OCR next-phase plan with ingestion workflow status.
- [x] 4.3 Document explicit non-goals and external provider boundary.

## 5. Verification

- [x] 5.1 Add focused backend ingestion tests.
- [x] 5.2 Add or update frontend diagnostics tests.
- [x] 5.3 Run focused backend provider, artifact, and ingestion tests.
- [x] 5.4 Run targeted frontend diagnostics tests.
- [x] 5.5 Run OpenSpec strict validation and archive completed change.
