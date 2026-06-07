## 1. Specification

- [x] 1.1 Create proposal, design, and spec delta for upload-file local operator entrypoint.
- [x] 1.2 Validate the OpenSpec change before implementation.

## 2. Backend Implementation

- [x] 2.1 Add upload materialization helper with safe filename, content hash, and controlled local output directory.
- [x] 2.2 Extend local trial API to accept upload payloads while preserving document path mode.
- [x] 2.3 Include upload materialization metadata in the operator result summary.

## 3. Frontend Implementation

- [x] 3.1 Add file picker state to the Settings diagnostics local document RAG card.
- [x] 3.2 Send uploaded file payloads to the local trial API and keep path mode as fallback.
- [x] 3.3 Display selected filename and materialized upload path in the result summary.

## 4. Verification

- [x] 4.1 Add focused backend tests for upload materialization, upload-mode router payload, invalid input, and path-mode compatibility.
- [x] 4.2 Add focused frontend tests for file upload trial payload and path fallback.
- [x] 4.3 Run focused backend and frontend tests.
- [x] 4.4 Run `openspec validate --all --strict`.

## 5. Archive

- [x] 5.1 Update concise docs/architecture notes with the upload-file operator entrypoint.
- [x] 5.2 Archive the OpenSpec change after implementation and validation.
