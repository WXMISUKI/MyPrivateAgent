## 1. Spec And Design

- [x] 1.1 Finalize dependency mapping and invocation hardening spec deltas.
- [x] 1.2 Record the shared dependency mapper decision in design.md and runtime contracts docs.

## 2. Backend Implementation

- [x] 2.1 Add a shared dependency mapper helper for registry detail, Workflow Lab, and invocation preflight.
- [x] 2.2 Expose dependency_mapping on workflow registry detail and reuse the same blocker taxonomy in Workflow Lab.
- [x] 2.3 Make workflow invocation fail closed on dependency mapping blockers before executor dispatch.

## 3. Verification

- [x] 3.1 Add focused backend tests for dependency mapping consistency and dependency-blocked invocation.
- [x] 3.2 Add or update a focused integration acceptance record under `docs/integration/`.
- [x] 3.3 Run strict OpenSpec validation and focused pytest.

## 4. Archive

- [ ] 4.1 Archive the change after implementation and validation complete.
