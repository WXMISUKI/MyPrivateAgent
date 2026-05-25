## 1. Read Model Boundary Hardening

- [x] 1.1 Update backend and docs to treat `main_chat_query_detail` as the primary single-query read model
- [x] 1.2 Update backend and docs to treat `main_chat_query_history` as the primary cross-query history read model
- [x] 1.3 Keep `recent_queries` explicitly documented as a lightweight summary list

## 2. Contract and Consumer Parity

- [x] 2.1 Align `RuntimeSurfacePanel` and `GovernanceTimelinePanel` with the same query/history normalization helpers
- [x] 2.2 Keep `runtime-profile` compatibility fields stable while using dedicated endpoints as the growth path
- [x] 2.3 Update query-related docs and roadmap entries to reflect the hardened read model boundary

## 3. Verification and Handoff

- [x] 3.1 Verify the read model spec does not contradict `runtime-core-terms-model`
- [x] 3.2 Re-read updated docs and spec artifacts for consistency
- [x] 3.3 Prepare the change for implementation once the spec passes self-review
