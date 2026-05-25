# ii2-runtime-contract-trace-approved-coverage

## Why

`runtime_contract_summary.approved_tool_execution_coverage` has become a stable backend summary field, but the degraded Runtime Contract Gate trace path still normalizes only approval replay coverage. This leaves trace payloads and dedupe fingerprints unable to distinguish whether approved tool bridge smoke coverage changed.

## What Changes

- Include normalized `approved_tool_execution_coverage` in `runtime_contract_gate_degraded` trace payloads.
- Include the same normalized coverage in Runtime Contract Gate degraded fingerprint / dedupe key generation.
- Keep missing or malformed coverage fail-closed as `bridge_smoke = false`.
- Update backend tests and runtime contract docs.

## Capabilities

### New Capabilities
- `runtime-contract-trace-approved-coverage`: Runtime Contract Gate degraded traces preserve approved tool bridge coverage and dedupe when that coverage changes.

### Modified Capabilities

## Impact

- 收口对象：`backend/routers/health.py` Runtime Contract Gate trace recording and fingerprint normalization.
- 后端 contract：`runtime_contract_gate_degraded.payload.runtime_contract_summary.approved_tool_execution_coverage` and corresponding dedupe fingerprint.
- 前端消费点：Governance Timeline can keep consuming `runtime_contract_summary`; no UI change in this slice.
- 文档真源：`docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`, `docs/test_manual.md`.
- 非目标：不改 smoke 执行、不改 `quality_gate_report.py` summary 生成、不新增前端展示。
