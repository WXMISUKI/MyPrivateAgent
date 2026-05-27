## Context

`RuntimeSurfaceService.get_runtime_profile()` now delegates the top-level profile shell to `RuntimeSurfaceProfileAssembler`, but the extracted assembler still mixes several concerns:

- provider catalog preparation
- main chat trace and query read model calls
- runtime scope construction
- recovery target selection
- child executor and embedded runtime contract assembly
- final profile shell construction

This change takes the smallest next step by extracting only profile request context/scope handling. That concern is stable, has no payload expansion requirement, and is easier to verify than child executor or recovery scheduler behavior.

## Goals / Non-Goals

**Goals:**

- Introduce a dedicated backend boundary for Runtime Surface profile context/scope assembly.
- Keep `RuntimeSurfaceProfileAssembler` focused on composing already-built sections into the top-level profile shell.
- Preserve all existing Runtime Profile fields and consumers.
- Add focused tests that protect delegation and recovery target precedence.

**Non-Goals:**

- No Runtime Profile public field additions or removals.
- No frontend changes.
- No database migration or compatibility key cleanup.
- No child executor replay, recovery scheduler, channel promotion, or production recovery behavior changes.

## Decisions

1. Add a concern-specific assembler module instead of adding helper methods to `RuntimeSurfaceProfileAssembler`.

   Rationale: the existing canonical spec asks for decomposable profile assembly by concern. A separate module gives future refactors a clear place for request context, runtime scope, and target derivation without growing the shell assembler again.

2. Keep the assembler service-aware for this slice.

   Rationale: `runtime_scope` is currently produced by `RuntimeSurfaceService._build_runtime_scope_contract(...)`. Moving that logic would broaden the change. The new assembler delegates to the existing service method and centralizes only the call boundary and target selection.

3. Preserve recovery target precedence.

   Rationale: the current behavior prefers `parent_run_id`, then `runtime_scope.scheduler_run_id`, then `runtime_scope.run_id`. The new boundary must retain that exact order to avoid changing recovery read model semantics.

## Risks / Trade-offs

- [Risk] Adding a wrapper without enough value could look like indirection.
  Mitigation: the wrapper owns a real concern: normalized input context, runtime scope construction, and recovery target derivation. Focused tests pin this behavior.

- [Risk] A future refactor might move too much runtime contract logic into the context assembler.
  Mitigation: docs and specs state that this assembler is limited to context/scope/target derivation, not profile payload construction.

- [Risk] Full `test_runtime_surface_service` currently has unrelated legacy failures.
  Mitigation: verify with focused tests for this seam and OpenSpec validation; do not fold unrelated behavioral fixes into this refactor.
