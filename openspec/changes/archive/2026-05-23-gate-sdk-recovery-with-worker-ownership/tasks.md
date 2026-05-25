## 1. Specification

- [x] 1.1 Define opt-in SDK worker ownership gate slice and non-goals.
- [x] 1.2 Define delta specs for ownership fail-closed and operation evidence.

## 2. Implementation

- [x] 2.1 Add optional `worker_ownership_store` injection to `EmbeddedAgentRuntimeSDK`.
- [x] 2.2 Add SDK helper to validate supplied worker ownership evidence.
- [x] 2.3 Pass validated ownership evidence into recovery operation records.
- [x] 2.4 Fail closed before executing recovered continuation when ownership validation fails.

## 3. Verification and Docs

- [x] 3.1 Add focused SDK worker ownership gate tests.
- [x] 3.2 Run focused SDK/Runtime Surface tests.
- [x] 3.3 Update architecture/roadmap/manual-test docs.
- [x] 3.4 Run OpenSpec strict validation.
- [x] 3.5 Sync canonical specs and archive the completed change.
