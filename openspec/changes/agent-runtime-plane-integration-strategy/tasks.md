## 1. Strategy Freeze

- [ ] 1.1 Add the runtime-plane integration strategy spec and delta specs to OpenSpec
- [ ] 1.2 Update project entrypoint docs to make the new control-plane vs runtime-plane split explicit
- [ ] 1.3 Update roadmap docs to show the freeze-and-align stage and the stage-gated rollout sequence

## 2. Contract Boundary Setup

- [ ] 2.1 Define the normalized execution envelope fields needed for runtime requests, events, results, interrupts, and errors
- [ ] 2.2 Add or update adapter boundary docs so framework-native payloads are not treated as public governance contracts
- [ ] 2.3 Confirm the directory boundary guidance for future `control_plane`, `runtime_plane`, and `framework_adapters` code

## 3. Runtime Slice Planning

- [ ] 3.1 Select the first minimal runtime-plane slice candidate and record the rationale
- [ ] 3.2 Define the smallest adapter-backed proof that can run without becoming a platform rewrite
- [ ] 3.3 Write the stage 0 and stage 1 review checklist for post-stage reflection

## 4. Validation and Review

- [ ] 4.1 Verify the new specs are readable and testable from OpenSpec status
- [ ] 4.2 Verify the updated docs clearly state the control-plane ownership and runtime-plane constraints
- [ ] 4.3 Review whether the next stage still fits the documented non-goals before implementation begins

## 5. Archive Readiness

- [ ] 5.1 Confirm the proposal, design, spec, and tasks are internally consistent
- [ ] 5.2 Prepare archive notes that summarize the freeze decision, adapter boundary, and next allowed action
- [ ] 5.3 Keep implementation out of scope until the runtime-plane slice is explicitly approved
