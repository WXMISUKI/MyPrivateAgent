---
name: myagent-contract-refactor
description: Refactor MyPrivateAgent backend runtime contracts, read models, assemblers, builders, or quality gates while preserving external contract shape. Use when changing RuntimeSurfaceService, runtime surface builders, runtime contracts, query/read models, SDK contracts, ToolRuntime, governance overview, contract snapshot, or smoke/quality gate paths.
---

# MyPrivateAgent Contract Refactor

Use this skill for backend refactors where contract stability matters more than local code movement.

## Required Guardrails

- Preserve external payload shape unless an OpenSpec change explicitly allows a contract change.
- Keep `RuntimeSurfaceService.get_runtime_profile()` as an orchestration entrypoint, not a dumping ground.
- Prefer concern-specific builders for model/provider catalog, governance overview, runtime core, recovery, query detail/history, and contract gate summaries.
- Do not remove compatibility fields without checking docs, frontend consumers, and snapshot guards.
- Keep fail-closed behavior for runtime contract gates, approval/recovery, and quality-gate artifact parsing.

## Standard Workflow

1. Read relevant context:
   - `docs/architecture/runtime_contracts.md`
   - `docs/roadmap/next_phase_hardening.md`
   - Relevant `openspec/specs/*/spec.md`
   - Existing focused tests under `tests/agent_framework/`
2. Identify the narrowest seam:
   - Extract builder/helper if behavior is stable.
   - Add a new contract field only if the spec or user request requires it.
   - Prefer adapting existing read models over adding parallel interpretations.
3. Add or update focused tests before or with the implementation:
   - Builder-level test for pure assembly.
   - Service-level test for returned profile shape.
   - Snapshot/smoke test when guarded contract fields change.
4. Implement minimal code movement:
   - Avoid broad renames.
   - Avoid database migrations unless the spec explicitly calls for one.
   - Do not mix unrelated cleanup into the slice.
5. Sync docs:
   - `docs/architecture/runtime_contracts.md` for stable contract boundaries.
   - `docs/roadmap/next_phase_hardening.md` for current state and next steps.
   - OpenSpec tasks/specs if an active change exists.
6. Verify with the smallest meaningful commands.

## Common Verification Commands

Use the narrowest applicable subset:

```powershell
conda run -n myenv python -m unittest tests.agent_framework.test_runtime_surface_service -v
conda run -n myenv python -m unittest tests.agent_framework.test_runtime_contract_gate_service tests.agent_framework.test_quality_gate_report -v
conda run -n myenv python -m unittest tests.agent_framework.test_embedded_runtime_sdk tests.agent_framework.test_tool_runtime_service -v
openspec validate --specs runtime-surface-contract-assembler --strict
openspec validate --strict
```

## Completion Criteria

- Focused tests pass.
- OpenSpec validation passes when a relevant spec/change is touched.
- Runtime docs explain the new seam.
- Public contract consumers do not need to change unless explicitly intended.
