## 1. Continuation Registry Contract

- [x] 1.1 Define a narrow continuation registry / resolver seam for Embedded SDK
- [x] 1.2 Extend continuation descriptors with stable binding identity fields
- [x] 1.3 Extend recovery reasons to distinguish registry-backed vs missing-binding cases

## 2. SDK Reattachment Implementation

- [x] 2.1 Persist binding ids when tool / loop continuations are registered
- [x] 2.2 Make `probe_run_recovery()` registry-aware
- [x] 2.3 Reattach tool continuation on approval recovery when binding is resolvable
- [x] 2.4 Reattach loop continuation on `resume_run(..., continue_loop=True)` when bindings are resolvable
- [x] 2.5 Keep legacy descriptors and unregistered callables fail-closed

## 3. Verification and Docs

- [x] 3.1 Add focused tests for recoverable-via-registry and missing-binding scenarios
- [x] 3.2 Re-run Embedded SDK / Harness / Workspace Store focused tests
- [x] 3.3 Update runtime contracts and roadmap, then mark tasks complete
