## Context

Runtime Surface assembly now has dedicated boundaries for:

- top-level profile shell
- profile context / runtime scope / recovery target derivation
- `runtime_core` contract assembly

`governance_overview.run` still duplicates much of the runtime scope projection inside `_build_governance_overview_contract()`. It is also the parent-facing surface where child merge state is consumed by governance UI. This makes it a good next concern-specific extraction before attempting a full governance overview builder.

## Goals / Non-Goals

**Goals:**

- Extract `governance_overview.run` assembly into a dedicated builder.
- Preserve all existing fields and fallback behavior.
- Keep `_build_governance_overview_contract()` responsible for the overall governance overview shell for now.
- Add focused tests that exercise the builder without needing recovery or child executor dispatch setup.

**Non-Goals:**

- No full `GovernanceOverviewContractBuilder` extraction.
- No recovery alignment changes.
- No child executor preflight, promotion gate, dispatch, or scheduler behavior changes.
- No Runtime Profile payload shape changes.

## Decisions

1. Extract only the run-state section.

   Rationale: the full governance overview contains several behavior-heavy sections. The run-state section is stable, pure, and directly tied to Runtime Core terminology.

2. Reuse `RuntimeCoreContractBuilder.build_child_merge_state_contract(...)`.

   Rationale: `runtime_core` and `governance_overview.run` expose the same child merge fields. Reusing the helper keeps the child merge projection consistent without coupling the two full contract sections.

3. Preserve the service method as a compatibility orchestration layer.

   Rationale: callers and the top-level profile assembler should not need to change beyond the internal run section delegation.

## Risks / Trade-offs

- [Risk] Run state builder could grow into a full governance overview builder accidentally.
  Mitigation: specs and docs limit this builder to `governance_overview.run`.

- [Risk] Child merge fields could drift from `runtime_core`.
  Mitigation: focused tests cover the child merge section evidence and service-level Runtime Surface integration.

- [Risk] Full service tests may include unrelated failures.
  Mitigation: verify with builder tests plus the known governance run-state integration test.
