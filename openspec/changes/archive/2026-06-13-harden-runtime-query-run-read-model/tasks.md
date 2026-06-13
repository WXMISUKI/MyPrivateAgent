## 1. Contract and Implementation Review

- [x] 1.1 Inspect backend query detail/history contracts and frontend shared interpretation usage for query/run identity drift.
- [x] 1.2 Identify the smallest implementation change needed to keep Runtime Surface and Governance Timeline aligned on shared read-model metadata.

## 2. Implementation

- [x] 2.1 Apply the minimal backend or frontend change needed to preserve `query_id` lifecycle identity and shared interpretation semantics.
- [x] 2.2 Add or update focused tests for the changed query read-model or interpretation behavior.

## 3. Documentation and Verification

- [x] 3.1 Update canonical spec/docs/roadmap to record the hardening boundary, non-goals, and completion line.
- [x] 3.2 Run focused tests and `openspec validate --all --strict`.
- [ ] 3.3 Archive the completed OpenSpec change after specs are synced.
