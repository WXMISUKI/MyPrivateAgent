## 1. Recovery Protocol Contract

- [x] 1.1 Define recovery status / reason helpers for tool and loop continuation descriptors
- [x] 1.2 Add a narrow recovery probe seam to `EmbeddedAgentRuntimeSDK`
- [x] 1.3 Keep `resume_run(..., continue_loop=True)` behind the same fail-closed recovery gate

## 2. Focused Implementation

- [x] 2.1 Persist recovery status / reason into run metadata and continuation descriptors
- [x] 2.2 Emit recovery-related status events for blocked or failed recovery attempts
- [x] 2.3 Keep current in-process executable continuation behavior unchanged when recovery is actually available

## 3. Verification and Docs

- [x] 3.1 Add focused unittest coverage for recoverable vs unrecoverable recovery probe results
- [x] 3.2 Re-run Embedded SDK / Harness / Workspace Store focused tests
- [x] 3.3 Update runtime contracts and roadmap to describe II-1.3 as formal recovery protocol, then mark tasks complete
