## 1. Specification

- [x] 1.1 Create proposal, design, and spec deltas for Runtime Surface runtime-plane profile
- [x] 1.2 Validate that the profile is read-only and does not execute adapters
- [x] 1.3 Confirm non-goals exclude trace persistence, approval submission, frontend UI, and default chat changes

## 2. Implementation

- [x] 2.1 Add a dedicated Runtime Surface runtime-plane profile builder
- [x] 2.2 Add top-level `runtime_plane_governance_profile` to Runtime Surface profile assembly
- [x] 2.3 Add Runtime Contract Snapshot guard fields for the new profile
- [x] 2.4 Add focused Runtime Surface and snapshot tests

## 3. Documentation

- [x] 3.1 Update runtime contracts and runtime-plane strategy docs
- [x] 3.2 Update next-phase roadmap with the completed slice and next allowed action
- [x] 3.3 Add a stage review document recording scope, evidence, drift checks, and follow-up

## 4. Verification And Archive

- [x] 4.1 Run `openspec validate add-runtime-surface-runtime-plane-profile`
- [x] 4.2 Run focused Runtime Surface and snapshot tests
- [x] 4.3 Archive the change after specs, implementation, docs, and tests are complete
