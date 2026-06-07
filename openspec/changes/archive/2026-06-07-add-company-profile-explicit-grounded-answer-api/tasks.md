## 1. Specification

- [x] 1.1 Create proposal, design, delta spec, and tasks for the explicit grounded-answer API.
- [x] 1.2 Validate the OpenSpec change before implementation.

## 2. Implementation

- [x] 2.1 Add a lightweight caller-facing response adapter for live grounded-answer reports.
- [x] 2.2 Add `POST /api/domain-agents/{agent_id}/live-grounded-answer`.
- [x] 2.3 Ensure provider API key values are accepted but never echoed.
- [x] 2.4 Update integration docs with the explicit API call and boundaries.

## 3. Verification And Archive

- [x] 3.1 Add focused tests for success, provider failure, source scoping, compact response, and API key redaction.
- [x] 3.2 Run focused router/service tests.
- [x] 3.3 Run `openspec validate add-company-profile-explicit-grounded-answer-api --strict`.
- [x] 3.4 Run a real local API smoke if the provider and backend app are reachable.
- [x] 3.5 Run `openspec validate --all --strict`.
- [x] 3.6 Archive the OpenSpec change after specs are synchronized.
