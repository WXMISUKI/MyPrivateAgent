## 1. Specification

- [x] 1.1 Create proposal, design, and spec deltas for runtime-plane governance read model
- [x] 1.2 Validate that the slice is limited to side-effect-free envelope projection
- [x] 1.3 Confirm non-goals exclude trace persistence, approval submission, Runtime Surface API wiring, frontend work, and default chat changes

## 2. Implementation

- [x] 2.1 Add a pure governance projection builder in `backend/runtime_plane/governance_bridge.py`
- [x] 2.2 Include `governance_projection` in simple/tool/approval adapter outputs
- [x] 2.3 Add focused tests for simple, tool, and approval projection behavior

## 3. Documentation

- [x] 3.1 Update runtime-plane strategy docs with the read-only governance projection step
- [x] 3.2 Update next-phase roadmap with the completed slice and next allowed action
- [x] 3.3 Add a review document recording scope, evidence, drift checks, and follow-up

## 4. Verification And Archive

- [x] 4.1 Run `openspec validate add-runtime-plane-governance-read-model`
- [x] 4.2 Run focused runtime-plane adapter and projection tests
- [x] 4.3 Archive the change after specs, implementation, docs, and tests are complete
