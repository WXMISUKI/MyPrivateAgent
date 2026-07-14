## 1. Specification

- [x] 1.1 Create proposal, design, spec, and task checklist for LangGraph smoke projection source.
- [x] 1.2 Validate the OpenSpec change before implementation.

## 2. Implementation

- [x] 2.1 Add `build_langgraph_smoke_governance_projection(...)` to `FrameworkAdapterRuntimeService`.
- [x] 2.2 Map blocked, passed, and failed smoke reports into compact runtime-plane projection fields.
- [x] 2.3 Preserve side-effect-free boundary flags and trace-backed evidence summary.

## 3. Tests

- [x] 3.1 Add focused test for passed smoke projection.
- [x] 3.2 Add focused test for blocked smoke projection.
- [x] 3.3 Add focused test for failed smoke projection with compact error evidence.

## 4. Documentation And Review

- [x] 4.1 Update runtime-plane architecture and next-phase roadmap docs.
- [x] 4.2 Add a review document confirming scope, evidence, and non-goals.

## 5. Verification And Archive

- [x] 5.1 Run focused OpenSpec and pytest verification.
- [x] 5.2 Archive the completed change and confirm no active OpenSpec change remains.
