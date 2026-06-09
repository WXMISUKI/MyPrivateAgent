## 1. Specification

- [ ] 1.1 Create the `align-provider-trial-outcome-with-phase25-feedback-contract` OpenSpec proposal, design, spec delta, and task list.

## 2. Implementation

- [ ] 2.1 Extend the unified knowledge provider repo-side trial outcome export with a Phase 25 feedback-compatible payload shape.
- [ ] 2.2 Keep the existing caller-side trial report readable while exposing the provider feedback fields explicitly.
- [ ] 2.3 Update focused tests to cover the new feedback-compatible output shape.

## 3. Documentation

- [ ] 3.1 Update MyPrivateAgent integration docs to explain that the repo-side trial outcome can be passed back into unifiedKnowledgeRAG Phase 25 feedback.

## 4. Validation And Archive

- [ ] 4.1 Run focused tests and `openspec validate --all --strict`.
- [ ] 4.2 Archive the change.
