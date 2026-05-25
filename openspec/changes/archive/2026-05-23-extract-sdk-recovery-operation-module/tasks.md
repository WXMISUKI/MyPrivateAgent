## 1. Specification

- [x] 1.1 Define the recovery operation Module extraction scope and compatibility rules.
- [x] 1.2 Validate OpenSpec change in strict mode.

## 2. Implementation

- [x] 2.1 Add `backend/agent_framework/recovery_operations.py` with operation constants/builders.
- [x] 2.2 Update `sdk.py` to import and delegate recovery operation construction.
- [x] 2.3 Keep SDK contract, probe, event, and Runtime Surface read model shapes unchanged.

## 3. Verification and Docs

- [x] 3.1 Run focused SDK and Runtime Surface tests.
- [x] 3.2 Update architecture/roadmap docs with the new Module seam.
- [x] 3.3 Run OpenSpec strict validation.
- [x] 3.4 Sync canonical specs and archive the completed change.
