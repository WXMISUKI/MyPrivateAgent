## 1. SDK Recovery Gate Evidence

- [x] 1.1 Add an explicit retry attempt metadata input path to SDK recovery entrypoints without changing default behavior.
- [x] 1.2 Reuse `build_recovery_retry_evidence(...)` when blocked recovery gates record operation evidence.
- [x] 1.3 Ensure retry evidence remains compact and omitted when no retry metadata is supplied.

## 2. Read Model And Docs

- [x] 2.1 Verify `run_recovery` operation history and audit summary consume SDK-produced retry evidence.
- [x] 2.2 Update runtime contract and roadmap docs with the ordered next-direction backlog.

## 3. Validation And Archive

- [x] 3.1 Add focused tests for `submit_approval` and `resume_run` retry evidence recording.
- [x] 3.2 Run focused tests and OpenSpec validation.
- [x] 3.3 Sync canonical specs and archive the change.
