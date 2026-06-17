## Context

Runtime Surface currently delegates several profile concerns to dedicated builders, including profile context, runtime core, provider catalog, and governance overview run-state assembly. Embedded SDK / Harness recovery and bootstrap contracts still have a looser boundary: `RuntimeSurfaceProfileAssembler` builds the embedded runtime bundle directly, while `RuntimeSurfaceService` owns dedicated bootstrap and run recovery wrapper methods.

This change closes that gap by adding a concern-specific builder facade for Embedded SDK / Harness Runtime Surface read models. The implementation should preserve existing lower-level builders and execution services, then route Runtime Surface assembly through the new boundary.

## Goals / Non-Goals

**Goals:**

- Create a dedicated builder boundary for Embedded SDK / Harness Runtime Surface read-model assembly.
- Preserve the existing payload shape for runtime profile, embedded runtime bootstrap, run recovery, default runtime recovery, and governance recovery projection.
- Keep compatibility wrappers in `RuntimeSurfaceService` where backend callers already use them.
- Add focused regression tests for contract stability.
- Update canonical docs/specs so future Runtime Surface assembler work knows this boundary exists.

**Non-Goals:**

- Do not move or rewrite the SDK execution loop, persistence engine, continuation registry, ToolRuntime execution, provider model-step adapter, or domain-agent execution.
- Do not change recovery eligibility, approval replay, resume behavior, worker ownership, retry scheduling, or bootstrap validation semantics.
- Do not add routes, frontend UI, database migrations, or new external dependencies.
- Do not broaden this into a full `GovernanceOverviewContractBuilder` extraction.

## Decisions

1. Introduce a facade-style builder instead of moving all existing recovery code.

   Rationale: `RuntimeRecoveryContractBuilder` and `EmbeddedRuntimeContractBundleBuilder` already encode stable normalization logic and are covered indirectly by existing tests. A facade boundary gives Runtime Surface a clearer concern-specific entrypoint without risking large mechanical moves.

   Alternative considered: move methods out of `runtime_surface_builders.py` into the new module immediately. Rejected for this slice because it increases diff size and import churn without changing the external contract.

2. Keep `RuntimeSurfaceService` wrapper methods stable.

   Rationale: `get_embedded_runtime_bootstrap()`, `get_run_recovery()`, and private recovery builders are already service-level seams for routers/tests/internal callers. They should delegate to the new builder but remain callable.

   Alternative considered: have callers import the new builder directly. Rejected because it would widen the public implementation surface and weaken service ownership.

3. Treat governance overview recovery projection as a consumer, not the owner, of recovery assembly.

   Rationale: governance overview should keep projecting compact recovery state from already-built contracts. The new builder owns Embedded SDK / Harness read-model assembly, while governance overview keeps its existing summary shape.

   Alternative considered: extract recovery projection into a full governance overview builder now. Rejected because that is a larger Runtime Surface split and not necessary to close the Embedded SDK/Harness assembler gap.

## Risks / Trade-offs

- Risk: Import cycles between service, profile assembler, and new builder. Mitigation: the new builder delegates only to existing low-level builders and receives normalized inputs; it must not import `RuntimeSurfaceService`.
- Risk: Contract drift hidden by facade indirection. Mitigation: focused tests assert top-level runtime profile fields, bootstrap validation field presence, and run recovery/default recovery contract versions/keys.
- Risk: Over-extraction into behavior code. Mitigation: keep the builder read-model only and explicitly avoid SDK execution, provider calls, persistence mutations, and default chat behavior changes.

## Migration Plan

1. Add the new builder module.
2. Rewire profile assembly and service wrapper methods to use it.
3. Run focused backend tests for Runtime Surface embedded runtime and recovery contracts.
4. Sync docs/specs and archive the change after validation.

Rollback is straightforward: restore the previous direct calls to `EmbeddedRuntimeContractBundleBuilder` and `RuntimeRecoveryContractBuilder`. No data migration is involved.
