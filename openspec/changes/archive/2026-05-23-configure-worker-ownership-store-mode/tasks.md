## 1. Specification

- [x] 1.1 Define ownership store mode configuration scope and non-goals.
- [x] 1.2 Add runtime worker ownership delta spec for configurable default store mode.

## 2. Implementation

- [x] 2.1 Add `WORKER_OWNERSHIP_STORE_MODE` configuration with conservative default.
- [x] 2.2 Update default worker ownership store construction to support memory, SQL fallback, and strict SQL modes.
- [x] 2.3 Expose ownership store mode and source from the embedded runtime factory contract.

## 3. Verification and Docs

- [x] 3.1 Add focused tests for mode selection, fallback, strict failure, and runtime contract visibility.
- [x] 3.2 Update runtime architecture and roadmap docs.
- [x] 3.3 Run focused ownership/runtime dependency tests.
- [x] 3.4 Run OpenSpec strict validation.
- [x] 3.5 Sync canonical specs and archive the completed change.
