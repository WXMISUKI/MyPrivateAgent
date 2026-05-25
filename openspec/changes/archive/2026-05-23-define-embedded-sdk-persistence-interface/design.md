## Context

The embedded runtime already has the pieces required for durable recovery:

- `EmbeddedRunWorkspaceStore` persists run snapshots, event logs, approval snapshots, and continuation descriptors.
- `EmbeddedRuntimeDependencies` and `EmbeddedRuntimeFactory` provide a shared dependency seam for SDK and facade bootstrap.
- `probe_run_recovery(...)` exposes checkpoint and resume cursor readiness.
- Runtime Surface and contract gates can already consume recovery coverage.

The remaining ambiguity is the persistence interface itself. A caller can see backend fields such as `durable` and `fallback_active`, but there is no single SDK-facing contract that says whether the current embedded runtime is memory-only, durable-ready, or durable-degraded. Without that interface, recovery behavior can remain technically correct while SDK/facade consumers still make unsafe assumptions.

## Goals / Non-Goals

**Goals:**

- Define the SDK-facing persistence posture contract.
- Make SDK and facade bootstrap report the same persistence profile through `EmbeddedRuntimeFactory`.
- Align persistence posture with recovery probe reasons and runtime surface contracts.
- Add smoke/gate coverage so durable-vs-memory drift is visible.
- Keep the interface small enough to implement in one focused backend slice.

**Non-Goals:**

- No distributed scheduler, worker lease, or cross-process lock manager.
- No new graph runtime or external harness migration.
- No persistence of Python callables or active stream objects.
- No new UI workspace unless backend evidence proves useful first.
- No broad database migration as part of the first slice.

## Decisions

### Decision 1: Persistence posture is a contract, not a display label

The interface will expose a machine-readable `persistence_posture` with at least:

- `memory_preview`
- `durable_ready`
- `durable_degraded`

Rationale: `durable=true` alone is not enough. A SQL backend in fallback mode must not be interpreted as cross-process-ready.

Alternative considered: let each consumer inspect `workspace_backend`. Rejected because that repeats interpretation logic across SDK, facade, Runtime Surface, and tests.

### Decision 2: Factory remains the default bootstrap source

SDK/facade construction should continue flowing through `EmbeddedRuntimeDependencies` and `EmbeddedRuntimeFactory` for default runtime paths.

Rationale: The factory already centralizes workspace store and continuation registry. Adding a parallel persistence configuration path would reintroduce drift.

Alternative considered: add persistence flags directly to every SDK/facade constructor. Rejected because flags would duplicate backend facts and make tests pass with impossible states.

### Decision 3: Recovery remains fail-closed

The persistence interface may report durable readiness, but actual recovery still depends on descriptor, checkpoint, cursor, approval state, and registry binding checks.

Rationale: Persistence posture describes storage capability; it does not execute recovery and must not bypass recovery gates.

Alternative considered: treat `durable_ready` as recoverable. Rejected because durable storage without a descriptor or registry binding is still not recoverable.

### Decision 4: First slice is backend contract and smoke coverage

The first implementation slice should update backend contracts and focused tests before adding any new governance UI.

Rationale: The project constitution prioritizes backend read model / contract convergence over frontend local interpretation.

## Risks / Trade-offs

- [Risk] Consumers may confuse persistence readiness with recovery readiness.  
  Mitigation: specs require `persistence_posture` and recovery probe reasons to remain separate fields.

- [Risk] Factory contract grows too broad.  
  Mitigation: keep persistence profile limited to workspace/backend/fallback/recovery posture fields.

- [Risk] Existing tests rely on memory preview defaults.  
  Mitigation: preserve memory default behavior and add explicit durable/fallback samples.

- [Risk] Quality gate evidence becomes noisy.  
  Mitigation: add a single focused smoke check rather than expanding every runtime smoke path.

## Migration Plan

1. Add builder/helper logic for normalizing persistence posture from workspace backend description.
2. Expose the normalized profile from factory / SDK-owned runtime contract path.
3. Thread the profile into Runtime Surface without changing existing recovery fields.
4. Add focused tests for memory, durable-ready, and durable-degraded/fallback cases.
5. Add a smoke/gate summary field only after the focused contract test exists.
6. Update runtime contracts, roadmap, and manual testing docs.

Rollback is straightforward because the first slice adds fields and checks without removing existing `workspace_backend`, `run_recovery`, or checkpoint/cursor fields.

## Open Questions

- Whether the first durable-ready sample should use the existing SQLAlchemy workspace store or a lightweight fake durable store in tests.
- Whether `persistence_posture` should live under the existing `embedded_runtime_factory` profile only, or also be copied into SDK-specific method/capability metadata.
- Whether future artifact persistence should be part of this interface or remain a separate artifact index contract.
