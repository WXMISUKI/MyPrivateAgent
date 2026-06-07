## 1. Specification

- [x] 1.1 Create proposal, design, and spec for the local document RAG readiness check.
- [x] 1.2 Validate the OpenSpec change before implementation.

## 2. Implementation

- [x] 2.1 Add a local document RAG readiness service with OCR, knowledge provider, and command prerequisite checks.
- [x] 2.2 Add CPU/GPU profile and timeout posture reporting.
- [x] 2.3 Add a CLI exporter for local readiness reports.

## 3. Verification

- [x] 3.1 Add focused tests for `go`, `review`, and `blocked` readiness decisions.
- [x] 3.2 Run focused backend tests for readiness plus adjacent document RAG loop tests.
- [x] 3.3 Run `openspec validate --all --strict`.

## 4. Archive

- [x] 4.1 Refresh local readiness report artifacts where local dependencies are available.
- [x] 4.2 Update architecture/docs notes with the new local readiness entry.
- [x] 4.3 Archive the OpenSpec change after implementation and validation.
