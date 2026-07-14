## 1. Specification

- [x] 1.1 Create proposal, design, delta spec, and task checklist for the adapter authoring template.
- [x] 1.2 Validate the OpenSpec change before implementation.

## 2. Implementation

- [x] 2.1 Extend `FrameworkAdapterRuntimeService.build_adapter_authoring_checklist(...)` with additive `authoring_template` output.
- [x] 2.2 Keep registered, blocked, and unknown adapter reviews side-effect-free and fail-closed.
- [x] 2.3 Add focused tests for template contents, Stage 1 proof mapping, governance profile mapping, and no trace/audit writes.

## 3. Documentation And Review

- [x] 3.1 Update runtime-plane architecture and next-phase roadmap docs to name the template as the next allowed adapter step.
- [x] 3.2 Add a stage review document confirming scope, evidence, and non-goals.

## 4. Verification And Archive

- [x] 4.1 Run focused OpenSpec and pytest verification.
- [x] 4.2 Archive the completed change and confirm no active OpenSpec change remains.
