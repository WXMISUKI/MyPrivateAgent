## 1. Specification

- [x] 1.1 Define recovery retry evidence implementation slice and non-goals.
- [x] 1.2 Define delta specs for retry policy exposure and operation retry payload support.

## 2. Implementation

- [x] 2.1 Add retry policy and reason classification helpers to `backend/agent_framework/recovery_operations.py`.
- [x] 2.2 Allow `build_recovery_operation_record(...)` to accept compact retry evidence.
- [x] 2.3 Preserve existing default operation payload behavior when no retry evidence is supplied.

## 3. Verification and Docs

- [x] 3.1 Add focused recovery retry protocol tests.
- [x] 3.2 Run focused SDK/Runtime Surface tests.
- [x] 3.3 Update architecture/roadmap/manual-test docs.
- [x] 3.4 Run OpenSpec strict validation.
- [x] 3.5 Sync canonical specs and archive the completed change.
