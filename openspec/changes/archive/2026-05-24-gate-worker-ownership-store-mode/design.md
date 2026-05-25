## Context

Worker ownership has moved from a draft recovery boundary to a runtime dependency with both in-memory and SQLAlchemy adapters. The latest completed slice added `WORKER_OWNERSHIP_STORE_MODE` with conservative defaults and observable runtime factory fields. The remaining v1 gap is that runtime contract smoke and quality gate consumers do not yet fail when this mode disappears or regresses.

The affected surface is cross-cutting but narrow: smoke emits evidence, quality gate summarizes it, Runtime Contract Gate normalizes it, and snapshot guards prevent silent drift.

## Goals / Non-Goals

**Goals:**

- Add runtime contract smoke evidence for worker ownership store mode.
- Summarize that evidence in `runtime_contract_summary.worker_ownership_store_mode_coverage`.
- Normalize and fail closed when old or dirty artifacts omit the coverage.
- Guard the new summary fields in Runtime Contract Snapshot.
- Keep docs aligned with the new gate expectation.

**Non-Goals:**

- Do not change the default from `memory_only`.
- Do not introduce database vendor lock semantics, advisory locks, automatic renewal, or scheduler worker claiming.
- Do not require SQL availability for local smoke beyond existing isolated test database patterns.
- Do not change SDK recovery ownership enforcement rules.

## Decisions

1. Add one smoke check named `worker_ownership_store_mode`.

   This keeps the quality gate model consistent with existing checks like `embedded_sdk_persistence_posture` and `subagent_lane_query_detail`. The check should assert the default runtime factory contract exposes `memory_only`, source, configurable bootstrap knobs, adapter kind, durability, and fallback evidence shape.

2. Put derived coverage under `runtime_contract_summary.worker_ownership_store_mode_coverage`.

   Quality gate consumers already rely on nested coverage objects for contract areas. A compact object with `mode_smoke`, `default_mode`, `default_adapter_kind`, `default_durable`, `strict_mode_status`, and `fallback_mode_status` is enough for v1 diagnostics without copying full contracts into the summary.

3. Treat missing or malformed coverage as not covered.

   Runtime Contract Gate should normalize old artifacts to `mode_smoke = false` rather than trusting raw artifact claims. This follows the existing fail-closed handling for approval lifecycle and checkpoint coverage.

4. Keep vendor lock semantics as a future slice.

   SQL-backed lease/fencing already exists, but production lock semantics require database-specific choices and operational rollout design. Mixing that into this smoke gate would blur the slice and increase verification cost.

## Risks / Trade-offs

- [Risk] Smoke tests could become brittle if they rely on a real application database.
  - Mitigation: prefer existing factory and test-local adapter seams; only assert contract fields required by the spec.
- [Risk] Adding another summary field increases artifact schema churn.
  - Mitigation: update quality gate, Runtime Contract Gate, snapshot service, and docs in the same slice.
- [Risk] Fallback evidence could be over-interpreted as production readiness.
  - Mitigation: keep coverage labels explicit and continue documenting that SQL fallback is diagnostic evidence, not distributed lock readiness.

