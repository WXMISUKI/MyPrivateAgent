## Context

`RuntimeSurfaceService.get_runtime_profile()` already delegates profile assembly to `RuntimeSurfaceProfileAssembler`, which is a good first step. The remaining issue is locality: the assembler is currently embedded in `runtime_surface_builders.py`, a file that also owns model/provider catalog, recovery contracts, query read models, channel summaries, and other builders.

This change is a low-risk boundary extraction. It should make the top-level profile shell easier to find and test without changing the runtime profile contract.

## Goals / Non-Goals

**Goals:**

- Move `RuntimeSurfaceProfileAssembler` into a dedicated module.
- Keep the public service method and payload unchanged.
- Preserve compatibility imports so existing code importing from `runtime_surface_builders` does not break in the same slice.
- Add a narrow test proving the service-level profile still includes key shell fields and flows through the assembler boundary.
- Sync roadmap and runtime contract docs.

**Non-Goals:**

- Do not decompose all runtime surface builders.
- Do not change runtime profile top-level keys.
- Do not alter `RuntimeContractSnapshotService` guards.
- Do not migrate database or API behavior.
- Do not touch frontend consumers.

## Decisions

1. Create `runtime_surface_profile_assembler.py` for the profile shell assembler.
   - This makes the main runtime surface entrypoint visible without forcing a broad builders refactor.
   - `runtime_surface_builders.py` can continue owning concern-specific builders.

2. Re-export `RuntimeSurfaceProfileAssembler` from `runtime_surface_builders.py` during this slice.
   - This avoids breaking existing imports and lets future cleanup happen separately.
   - The service can import from the dedicated module directly.

3. Keep the assembler API unchanged.
   - The method continues to accept the service instance plus scoped parameters.
   - That keeps behavior stable and avoids a larger dependency injection redesign.

## Risks / Trade-offs

- [Risk] Moving a class can create import cycles because the assembler depends on other builders.
  -> Mitigation: keep concern-specific builders in `runtime_surface_builders.py` and import them into the dedicated assembler module.
- [Risk] The assembler still calls many service private helpers.
  -> Mitigation: this slice only establishes locality; deeper helper extraction remains a later II-3 task.
- [Risk] Compatibility imports obscure the new boundary.
  -> Mitigation: the service imports the dedicated module directly, while the old module only re-exports for compatibility.
