## 1. Specification

- [x] 1.1 Define recovery audit trace writer implementation slice and non-goals.
- [x] 1.2 Define delta spec for trace correlation and idempotent writer behavior.

## 2. Implementation

- [x] 2.1 Add `backend/services/recovery_audit_timeline_service.py`.
- [x] 2.2 Build compact trace payload from recovery operation evidence.
- [x] 2.3 Implement dedupe skip and fail-open behavior.

## 3. Verification and Docs

- [x] 3.1 Add focused recovery audit timeline service tests.
- [x] 3.2 Run focused recovery/audit tests.
- [x] 3.3 Update architecture/roadmap/manual-test docs.
- [x] 3.4 Run OpenSpec strict validation.
- [x] 3.5 Sync canonical specs and archive the completed change.
