## 1. Specification

- [x] 1.1 Create proposal, design, delta spec, and task checklist for LangGraph controlled pilot readiness.
- [x] 1.2 Validate the OpenSpec change before implementation.

## 2. Implementation

- [x] 2.1 Add a side-effect-free LangGraph controlled pilot readiness builder to `FrameworkAdapterRuntimeService`.
- [x] 2.2 Compose readiness from adapter registry, precheck, authoring template, Stage 1 proof mapping, and boundary checks.
- [x] 2.3 Keep unknown and unsupported adapters fail-closed without external runtime calls.

## 3. Tests

- [x] 3.1 Add focused tests for ready LangGraph readiness.
- [x] 3.2 Add focused tests for disabled external pilot, unknown adapter, and registered unsupported adapter blockers.
- [x] 3.3 Assert readiness generation does not write trace/audit.

## 4. Documentation And Review

- [x] 4.1 Update runtime-plane architecture and next-phase roadmap docs with the new next allowed action.
- [x] 4.2 Add a review document confirming scope, evidence, and non-goals.

## 5. Verification And Archive

- [x] 5.1 Run focused OpenSpec and pytest verification.
- [x] 5.2 Archive the completed change and confirm no active OpenSpec change remains.
