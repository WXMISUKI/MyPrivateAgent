## 1. Specification

- [x] 1.1 Create proposal, design, spec, and task checklist for LangGraph controlled pilot smoke.
- [x] 1.2 Validate the OpenSpec change before implementation.

## 2. Implementation

- [x] 2.1 Add `run_langgraph_controlled_pilot_smoke(...)` to `FrameworkAdapterRuntimeService`.
- [x] 2.2 Gate external execution through `build_langgraph_controlled_pilot_readiness(...)`.
- [x] 2.3 Summarize acceptance evidence without creating a new execution path.

## 3. Tests

- [x] 3.1 Add focused test for readiness-blocked smoke with no external call.
- [x] 3.2 Add focused test for successful smoke using stub external transport.
- [x] 3.3 Add focused test for failed external pilot captured as smoke evidence.

## 4. Documentation And Review

- [x] 4.1 Update runtime-plane architecture and next-phase roadmap docs.
- [x] 4.2 Add a review document confirming scope, evidence, and non-goals.

## 5. Verification And Archive

- [x] 5.1 Run focused OpenSpec and pytest verification.
- [x] 5.2 Archive the completed change and confirm no active OpenSpec change remains.
