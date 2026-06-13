## Context

`main_chat` already has query-level visibility through `main_chat_trace_overview`, dedicated query detail, dedicated query history, and the Governance Timeline workspace. The remaining risk is not missing UI surface area; it is semantic drift between backend read models, frontend interpretation helpers, and documentation.

This change is a hardening slice. It keeps the existing behavior shape and focuses on making the current `query_id` lifecycle read models easier to maintain and verify.

## Goals / Non-Goals

**Goals:**

- Keep `query_id` as the lifecycle key and `run_id` as an associated execution-instance field.
- Keep `main_chat_query_detail` and `main_chat_query_history` as dedicated read-model boundaries.
- Ensure frontend consumers share the same interpretation helper for query detail/history metadata.
- Document the completion line so future work does not keep expanding `main_chat` local UI after this phase.
- Verify through focused tests and strict OpenSpec validation.

**Non-Goals:**

- No provider-side RAG enhancement.
- No default `/api/chat` retrieval injection.
- No new channel promotion to full history/workspace.
- No database migration.
- No broad Governance Timeline or Runtime Surface redesign.

## Decisions

1. Treat this as a hardening change to `query-run-read-model`, not a new capability.
   - Rationale: the core read-model endpoints and workspace already exist; the next value is consistency and guardrails.
   - Alternative considered: create a new `runtime-query-read-model-hardening` capability. Rejected because it would split the truth source unnecessarily.

2. Prefer backend read-model fields over frontend reconstruction.
   - Rationale: the constitution and roadmap both require contract-first governance views.
   - Alternative considered: keep deriving missing labels from timeline events in each component. Rejected because it reintroduces duplicated interpretation rules.

3. Keep shared frontend interpretation as a facade, not a domain authority.
   - Rationale: `governanceViewInterpretation.js` should normalize contract display state, while backend contracts remain the truth source.
   - Alternative considered: move every display label into backend. Rejected because the current slice does not need to turn display formatting into API surface.

4. Use focused tests only.
   - Rationale: the change targets read-model/interpretation boundaries and docs, not a production build or broad runtime behavior.
   - Alternative considered: run full frontend build. Rejected unless implementation reveals a high-risk frontend contract change.

## Risks / Trade-offs

- [Risk] Existing components may still contain small fallback paths for old payloads. -> Mitigation: only remove or redirect fallback logic when the backend field is already stable and tests can cover it.
- [Risk] Over-hardening could accidentally imply generic multi-channel workspace readiness. -> Mitigation: specs and docs explicitly keep non-`main_chat` channels out of full history/workspace promotion.
- [Risk] Docs may overstate implementation maturity. -> Mitigation: roadmap wording will mark this as a focused hardening slice, not production expansion.
