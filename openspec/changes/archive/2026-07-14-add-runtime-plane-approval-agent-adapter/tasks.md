## 1. Specification

- [x] 1.1 Create proposal, design, and spec deltas for the approval-agent adapter slice
- [x] 1.2 Validate that the slice is limited to approval-pending envelope normalization
- [x] 1.3 Confirm non-goals exclude production approval submission, resume, default chat changes, scheduler, sandbox, and managed runtime integration

## 2. Implementation

- [x] 2.1 Add `ApprovalAgentAdapter` under `backend/runtime_plane/adapters/`
- [x] 2.2 Export the adapter through runtime-plane package entrypoints
- [x] 2.3 Add deterministic tests for health, approval-pending envelope, compact metadata, and no high-risk handler execution

## 3. Documentation

- [x] 3.1 Update runtime-plane strategy docs to mark approval-agent as the third Stage 1 slice
- [x] 3.2 Update next-phase roadmap with the decision and next allowed action
- [x] 3.3 Add a stage review document recording scope, evidence, drift checks, and follow-up

## 4. Verification And Archive

- [x] 4.1 Run `openspec validate add-runtime-plane-approval-agent-adapter`
- [x] 4.2 Run focused runtime-plane adapter tests
- [x] 4.3 Archive the change after specs, implementation, docs, and tests are complete
