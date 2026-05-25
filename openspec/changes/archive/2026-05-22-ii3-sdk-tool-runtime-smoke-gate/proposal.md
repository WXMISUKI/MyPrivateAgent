## Why

`ii3-embedded-sdk-tool-runtime-execution-bridge` has made `EmbeddedAgentRuntimeSDK.execute_run(...)` capable of using `ToolRuntimeService` directly, but the runtime contract smoke gate still proves only the older Facade bridge. This leaves the new SDK-first execution path protected by unit tests but not by the machine-readable quality gate artifact.

## What Changes

- Add a runtime contract smoke check for the SDK direct `register_tool -> execute_run(tool_policy) -> ToolRuntimeService` path.
- Expose dedicated quality gate summary coverage for the SDK ToolRuntime bridge so Runtime Profile consumers do not need to scan raw smoke checks.
- Keep the existing Facade approved-tool bridge smoke intact.
- Update runtime contract docs and manual test docs to describe the new gate evidence.

收口对象：SDK direct ToolRuntimeService execution bridge smoke coverage and quality gate summary.

非目标：

- Do not change ToolRuntimeService execution semantics.
- Do not change Facade bridge behavior.
- Do not add frontend UI.
- Do not archive completed OpenSpec changes in this change.

## Capabilities

### New Capabilities

- `sdk-tool-runtime-smoke-gate`: Runtime contract smoke and quality gate coverage for the SDK direct ToolRuntimeService execution bridge.

### Modified Capabilities

- `quality-gate-artifact-schema-guard`: Add a required runtime contract summary field for SDK ToolRuntime bridge coverage.

## Impact

- Backend scripts: `backend/scripts/runtime_contract_smoke.py`, `backend/scripts/quality_gate_report.py`
- Backend services: `backend/services/runtime_contract_gate_service.py`, `backend/services/runtime_contract_snapshot_service.py`
- Tests: focused runtime contract smoke, quality gate report, runtime contract gate, snapshot tests
- Docs: `docs/architecture/runtime_contracts.md`, `docs/test_manual.md`, `docs/roadmap/next_phase_hardening.md`
