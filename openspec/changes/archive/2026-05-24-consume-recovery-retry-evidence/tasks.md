## 1. Retry Evidence

- [x] 1.1 Add a recovery retry evidence helper/classifier in `backend/agent_framework/recovery_operations.py`.
- [x] 1.2 Ensure terminal, retryable, and exhausted retry states preserve compact idempotency evidence.

## 2. Read Model Consumption

- [x] 2.1 Extend recovery audit summary to expose latest retry status and latest retry terminal reason.
- [x] 2.2 Ensure `run_recovery` preserves retry summary evidence without executable internals.

## 3. Tests And Docs

- [x] 3.1 Add focused retry protocol and recovery audit summary tests.
- [x] 3.2 Update runtime contract and roadmap docs to record the retry evidence consumption boundary.
- [x] 3.3 Run focused tests and OpenSpec validation, then sync specs and archive the change.
