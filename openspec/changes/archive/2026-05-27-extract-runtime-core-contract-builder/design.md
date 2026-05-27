## Context

Runtime Surface assembly has started moving toward explicit concern boundaries:

- `RuntimeSurfaceProfileAssembler` owns the top-level profile shell.
- `RuntimeSurfaceProfileContextAssembler` owns request context, runtime scope, and recovery target derivation.
- `ProviderCatalogBuilder` owns model/provider catalog assembly.

The next low-risk concern is `runtime_core`: it is a compact contract shell built from an optional `runtime_scope`, and it is central to the `run_id` versus `query_id` terminology boundary.

## Goals / Non-Goals

**Goals:**

- Extract Runtime Core payload construction into a dedicated builder.
- Keep the service wrapper available for existing internal callers.
- Preserve all existing `runtime_core` fields and values.
- Add focused tests that can run without full Runtime Surface integration.

**Non-Goals:**

- No field additions, removals, or renames.
- No query detail/history behavior change.
- No governance overview builder extraction in this slice.
- No child executor merge semantics change.

## Decisions

1. Put the builder in a backend service builder boundary and keep it pure.

   Rationale: the builder only needs a `runtime_scope` dict and a child merge defaults/overlay helper. Keeping it pure makes it easy to test and avoids broad service mocking.

2. Preserve `_build_runtime_core_contract()` as a wrapper.

   Rationale: this avoids touching callers and lets the refactor be a pure internal movement with unchanged public profile output.

3. Move child merge state normalization with the Runtime Core builder.

   Rationale: `runtime_core` and `governance_overview.run` both expose child merge evidence. This slice only moves the `runtime_core` side, but keeping the helper next to the builder clarifies that merge state is part of the Runtime Core section payload, not top-level profile assembly.

## Risks / Trade-offs

- [Risk] Moving child merge normalization could accidentally change fallback behavior.
  Mitigation: focused tests cover default merge fields and scoped overlay fields, including `child_display_id`.

- [Risk] This may duplicate logic temporarily with governance overview run state.
  Mitigation: duplication already exists in the output surfaces; this slice does not change governance overview and leaves that as a later, explicit builder extraction.

- [Risk] Full runtime surface service tests may still contain unrelated legacy failures.
  Mitigation: run focused builder/wrapper tests plus OpenSpec validation, and avoid folding unrelated fixes into this slice.
