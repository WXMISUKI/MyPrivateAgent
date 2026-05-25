## Context

`RuntimeSurfaceService.get_runtime_profile()` is the broadest contract assembly path in the backend. It currently aggregates model/provider state, runtime scope, recovery, governance overview, query read models, tool/runtime contracts, and snapshot materialization in one method. The contract is stable, but the internal assembly boundary is too concentrated.

## Goals / Non-Goals

**Goals:**
- Extract the most complex runtime profile assembly logic into an explicit assembler/builder boundary.
- Keep `get_runtime_profile()` behavior and payload shape stable.
- Make the runtime profile easier to extend and test by concern.
- Preserve the current backend truth sources and docs alignment.

**Non-Goals:**
- No frontend redesign.
- No API contract change for `runtime_profile`.
- No new runtime capability beyond the refactor boundary.
- No database migration or persistence redesign.

## Decisions

- Keep `RuntimeSurfaceService` as the orchestration entrypoint, but move bulk assembly into a dedicated assembler. This preserves call sites while reducing method size.
- Prefer concern-based extraction over one giant new abstraction. The first split should follow the existing runtime profile seams: providers/models, governance/read models, recovery, child executor, and snapshot materialization.
- Keep helper names close to existing contract names so the mapping stays obvious for maintainers and tests.

Alternatives considered:
- Leave `get_runtime_profile()` as-is: rejected because it keeps the service monolith growing.
- Split the entire service into many tiny services immediately: rejected because it increases migration risk and obscures the first boundary.
- Refactor only a single helper: rejected because the method is already large enough that a minimal but meaningful assembler boundary is warranted.

## Risks / Trade-offs

- [Low] Slight temporary duplication during extraction -> Mitigation: keep the public service method as a thin orchestrator while helpers move out incrementally.
- [Low] Test expectations may need minor reshaping -> Mitigation: keep contract assertions focused on payload shape, not implementation details.
- [Low] New assembler boundary may become another catch-all -> Mitigation: split by concern and keep the initial boundary narrow.
