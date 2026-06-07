## 1. Specification

- [x] 1.1 Create proposal, design, and specs for the local document RAG upload-to-use loop.
- [x] 1.2 Validate the OpenSpec change before implementation.

## 2. Implementation

- [x] 2.1 Add a local document RAG upload-to-use loop service that reuses `DocumentIngestionService`.
- [x] 2.2 Convert OCR/Layout artifacts into normalized parser artifact handoff JSON.
- [x] 2.3 Add injectable provider-side ingestion command execution.
- [x] 2.4 Reuse the existing local knowledge provider corpus trial for provider usability verification.
- [x] 2.5 Add a CLI exporter for local operator runs.

## 3. Verification

- [x] 3.1 Add focused tests for `go`, ingestion failure, no-text artifact, handoff-only review, provider command failure, and corpus trial review/blocking.
- [x] 3.2 Run focused backend tests for document ingestion, local knowledge provider corpus trial, and the new upload-to-use loop.
- [x] 3.3 Run `openspec validate --all --strict`.

## 4. Archive

- [x] 4.1 Refresh local report artifacts for the upload-to-use loop where local dependencies are available.
- [x] 4.2 Update architecture/docs notes with the new local trial loop and next action.
- [x] 4.3 Archive the OpenSpec change after implementation and validation.
