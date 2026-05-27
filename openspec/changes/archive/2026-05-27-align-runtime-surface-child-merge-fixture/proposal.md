## Why

`test_runtime_profile_surfaces_backend_governance_run_state` exposes a real drift between the Runtime Surface integration fixture and the current child executor execution contract. The fixture expects merged `risk_review` semantics, but it does not provide the explicit executor binding opt-in now required by the fail-closed child executor gate, so the child execution is blocked and Runtime Surface falls back to default `general_analysis` semantics.

收口对象：Runtime Surface child merge integration fixture 与当前 child executor execution prerequisites 的一致性。非目标：不放宽 fail-closed gate，不改变 production child executor dispatch，不修改 Runtime Profile payload shape。

## What Changes

- Align the Runtime Surface governance run state fixture with the explicit child executor binding opt-in contract.
- Keep the child executor execution gate fail-closed for callers that omit opt-in evidence.
- Preserve existing Runtime Surface `runtime_core` and `governance_overview.run` child merge fields.
- Add or update focused verification so the previously failing test passes under the current contract.
- Sync OpenSpec and docs to make the fixture requirement explicit.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `child-executor-execution-prerequisites`: clarify that tests expecting executed child merge semantics MUST provide explicit executor binding opt-in evidence.
- `governance-overview-run-state-surface`: clarify that Runtime Surface run-state integration fixtures must satisfy child executor execution prerequisites before asserting merged child semantics.

## Impact

- Tests:
  - `tests/agent_framework/test_runtime_surface_service.py`
- Docs/specs:
  - `openspec/specs/child-executor-execution-prerequisites/spec.md`
  - `openspec/specs/governance-overview-run-state-surface/spec.md`
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`
- Runtime behavior:
  - No public runtime contract change.
