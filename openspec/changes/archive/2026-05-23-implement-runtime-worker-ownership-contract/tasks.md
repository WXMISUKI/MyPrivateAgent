## 1. Specification

- [x] 1.1 Define worker ownership implementation slice and non-goals.
- [x] 1.2 Define delta specs for ownership adapter seam and recovery operation payload support.

## 2. Implementation

- [x] 2.1 Add `backend/agent_framework/worker_ownership.py` with contract, lease record, and in-memory store.
- [x] 2.2 Allow `build_recovery_operation_record(...)` to accept compact worker ownership evidence.
- [x] 2.3 Preserve existing default `worker_ownership.implemented=false` behavior when no ownership evidence is supplied.

## 3. Verification and Docs

- [x] 3.1 Add focused worker ownership and recovery operation payload tests.
- [x] 3.2 Run focused SDK/Runtime Surface tests.
- [x] 3.3 Update architecture/roadmap/manual-test docs.
- [x] 3.4 Run OpenSpec strict validation.
- [x] 3.5 Sync canonical specs and archive the completed change.
