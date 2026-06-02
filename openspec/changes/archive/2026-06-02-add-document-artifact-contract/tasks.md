## 1. Spec

- [x] 1.1 Create OpenSpec proposal and design for document artifact/provenance contract.
- [x] 1.2 Add `unified-capability-runtime` requirement delta for artifact persist/read/list and diagnostics action.

## 2. Backend

- [x] 2.1 Add document artifact service with local metadata and payload persistence.
- [x] 2.2 Add compact payload normalization for OCR/Layout/VLM results.
- [x] 2.3 Add `POST /api/document-artifacts`, `GET /api/document-artifacts`, and `GET /api/document-artifacts/{artifact_id}`.
- [x] 2.4 Return structured `DOCUMENT_ARTIFACT_NOT_FOUND` errors.

## 3. Frontend

- [x] 3.1 Add document artifact API wrapper.
- [x] 3.2 Add diagnostics persist action for successful OCR/Layout/VLM results.
- [x] 3.3 Display persisted `artifact_id` and structured errors.

## 4. Docs

- [x] 4.1 Add document artifact usage guide and API examples.
- [x] 4.2 Update OCR next-phase plan with artifact slice status.

## 5. Verification

- [x] 5.1 Add focused backend tests for persist/read/list, raw exclusion, and missing artifact.
- [x] 5.2 Run focused backend provider and artifact tests.
- [x] 5.3 Run lightweight frontend syntax or targeted test if available.
