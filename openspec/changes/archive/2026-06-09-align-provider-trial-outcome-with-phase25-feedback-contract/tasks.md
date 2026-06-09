## 1. Specification

- [x] 1.1 Create the `align-provider-trial-outcome-with-phase25-feedback-contract` OpenSpec proposal, design, spec delta, and task list.

## 2. Implementation

- [x] 2.1 Extend the unified knowledge provider repo-side trial outcome export with a Phase 25 feedback-compatible payload shape.
- [x] 2.2 Keep the existing caller-side trial report readable while exposing the provider feedback fields explicitly.
- [x] 2.3 Update focused tests to cover the new feedback-compatible output shape.

## 3. Documentation

- [x] 3.1 Update MyPrivateAgent integration docs to explain that the repo-side trial outcome can be passed back into unifiedKnowledgeRAG Phase 25 feedback.

## 4. Validation And Archive

- [x] 4.1 Run focused tests and `openspec validate --all --strict`.
- [x] 4.2 Archive the change.
