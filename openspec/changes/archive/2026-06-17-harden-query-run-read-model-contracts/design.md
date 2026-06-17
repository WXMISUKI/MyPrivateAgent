## Context

Runtime Surface already exposes `main_chat_query_detail`, `main_chat_query_history`, `recent_queries`, and `run_recovery`, but the project still carries some history/detail interpretation pressure in the UI and service layer. The next safe step is to harden the read-model contract boundary so these payloads stay canonical and do not drift into frontend-local reconstruction.

The change is intentionally narrow. It does not add new channels or new runtime behavior. It aligns existing query/run/recovery read models with the architecture direction already documented in `docs/architecture/runtime_contracts.md` and `docs/roadmap/next_phase_hardening.md`.

## Goals / Non-Goals

**Goals:**

- Preserve the distinct semantics of `query`, `run`, and recovery operation read models.
- Keep `main_chat_query_detail` and `main_chat_query_history` separate and stable.
- Keep `recent_queries` lightweight and backward compatible.
- Keep `run_recovery` compact, non-executable, and governed by the existing recovery read model boundary.
- Align Runtime Surface and Governance Timeline interpretation with the same normalization rules.

**Non-Goals:**

- Do not add a new channel read model family.
- Do not modify SDK execution, provider execution, or default chat retrieval behavior.
- Do not introduce database schema migration, persistent cursor state, or long-history pagination redesign.
- Do not widen `runtime-profile` into a catch-all query workspace.

## Decisions

1. Keep this as a contract-hardening slice, not a new feature slice.

   Rationale: the existing read models already exist. The risk is drift, not missing capability. Tightening the contract boundary gives the most value with the least surface area.

   Alternative considered: a broader query workspace extraction. Rejected because it would combine too many concerns and slow the closure of the current phase.

2. Use existing service seams rather than a new persistence layer.

   Rationale: the current `RuntimeSurfaceService` and builders already produce the needed contracts. A new storage or indexing layer would be unnecessary for this slice.

   Alternative considered: add a dedicated query history store. Rejected because the current issue is contract clarity, not storage absence.

3. Keep interpretation shared at the consumer boundary.

   Rationale: `RuntimeSurfacePanel` and `GovernanceTimelinePanel` should not separately redefine query/run terms.

   Alternative considered: separate interpretation helpers per panel. Rejected because it would reintroduce divergence.

## Risks / Trade-offs

- [Risk] Shared interpretation may hide subtle consumer-specific needs → [Mitigation] keep the helper canonical for shared fields only and retain local display adapters for layout.
- [Risk] Contract hardening may expose missing tests → [Mitigation] add focused regression coverage for detail/history/recovery outputs.
- [Risk] Overlapping read-model docs may cause ambiguity → [Mitigation] align architecture doc and roadmap note with the spec change in the same archive step.

## Migration Plan

1. Add or adjust the read-model contracts and tests.
2. Verify the existing detail/history/recovery outputs remain stable.
3. Update docs/specs to reflect the hardening boundary.
4. Archive the change.

Rollback is trivial: revert the read-model hardening adjustments and keep the existing payloads. No data migration is required.
