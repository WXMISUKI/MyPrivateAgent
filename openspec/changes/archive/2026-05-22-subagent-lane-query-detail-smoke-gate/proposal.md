# subagent-lane-query-detail-smoke-gate

## Why

`subagent_lane query detail` is now a backend contract, but it is not yet represented in runtime contract smoke output or the quality gate summary. That leaves the endpoint usable but not continuously guarded by the same machine-readable gate that already covers approval lifecycle, recovery, and approved tool execution.

## What Changes

- Add a runtime contract smoke check for `/api/runtime-profile/subagent-lane-query-detail`.
- Include a machine-readable `subagent_lane_query_detail_coverage` summary in quality gate and runtime contract gate outputs.
- Render the new coverage in the markdown quality gate summary.
- Keep scope backend-only and avoid adding frontend panels in this slice.

## Capabilities

### New Capabilities
- `subagent-lane-query-detail-smoke-gate`: proves `subagent_lane query detail` is present in smoke/gate outputs.

### Modified Capabilities
- `subagent-lane-query-detail-contract`: promoted from endpoint-level contract to smoke/gate-observed contract.

## Impact

- 收口对象：`runtime_contract_smoke.py`, `quality_gate_report.py`, `RuntimeContractGateService`, focused backend tests, runtime contract docs.
- 后端 contract：runtime smoke check name `subagent_lane_query_detail`.
- 前端消费点：none required in this slice.
- 非目标：不新增 `subagent_lane query history`、不做 workspace、不中断 child executor output replay / summary / merged semantics。
