## 1. Contract

- [x] 1.1 Define a machine-readable child executor preflight contract in the SDK / runtime surface layer
- [x] 1.2 Surface preflight readiness, blockers, and next step through runtime profile and governance overview

## 2. Implementation

- [x] 2.1 Build the backend preflight result from binding catalog, merge semantics, and backend readiness signals
- [x] 2.2 Expose the backend preflight result in `governance_overview` / child executor related runtime contracts
- [x] 2.3 Update Runtime Surface to render the preflight contract without recomputing promotion readiness

## 3. Verification and Docs

- [x] 3.1 Add focused backend/frontend assertions for ready and blocked preflight paths
- [x] 3.2 Run focused tests only
- [x] 3.3 Update runtime contracts and roadmap with the finalized preflight boundary
